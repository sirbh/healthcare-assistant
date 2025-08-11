from langgraph.graph import MessagesState
from langgraph.store.base import BaseStore
from langchain_core.runnables.config import RunnableConfig
from langchain.schema import SystemMessage

from enum import Enum
from pydantic import BaseModel, Field
from typing import List

from app.model.chatmodel import llm

from .retriever import retrieve
from app.agents.evaluater_agent import check_documents
from app.agents.diagnostic_agent import diagnose_condition
from app.agents.recommender_agent import recommend_treatment
from app.agents.explaination_agent import explain_diagnosis



class ExtendedMessagesState(MessagesState):
    summary: str

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class UserProfile(BaseModel):
    """User profile schema with typed fields"""
    user_name: str = Field(description="The user's preferred name")
    age: int = Field(description="The user's age")
    gender: Gender = Field(..., description="The user's gender: male, female, or other")
    conditions: List[str] = Field(
        default_factory=list,
        description="List of medical conditions the user has"
    )



llm_with_tool = llm.bind_tools([
    retrieve,
    check_documents,
    diagnose_condition,
    recommend_treatment,
    explain_diagnosis
])


def supervisor(state: ExtendedMessagesState,config: RunnableConfig, store: BaseStore):

    summary = state.get("summary", "")

    prompt = """
You are a medical assistant specialized in understanding user-described symptoms.
If the user asks non-medical questions, politely tell them to ask about their symptoms.

### REQUIRED BEHAVIOR (must-follow)
- You **must continuously ask for user symptoms** until the user explicitly says "no", "no more symptoms", or equivalent.
- **Do not** begin retrieval or follow-up-question generation until the user has finished listing symptoms (i.e., said "no more symptoms").
- For **every** symptom the user provides you **MUST**:
    1. Rewrite the user's plain-language description into clear medical terminology. (This rewritten term is what you will pass to the retrieve tool.)
    2. Call the `retrieve` tool with the rewritten medical-term symptom.
    3. Immediately call the `check_documents` tool on the documents returned by `retrieve`.
    4. If `check_documents` marks the documents as **relevant**, generate follow-up questions from those retrieved documents and ask **all** those follow-up questions for that symptom (one question at a time), waiting for the user's answer before asking the next question.
    5. If `check_documents` marks the documents as **not relevant** (or no documents were found), add that symptom to a "no information found" list and do **not** ask follow-up questions for that symptom.
- You must process symptoms **sequentially in the order the user provided them**: rewrite → retrieve → check_documents → (ask follow-ups if relevant) → proceed to next symptom.

### INFORMING THE USER
- After processing all symptoms:
  - If any symptoms were added to the "no information found" list, tell the user:
    "I don't have information about these symptoms: [list]. I can assist you with the other symptoms for which I found relevant documents."
  - For symptoms with relevant documents, you must have already asked **all** follow-up questions (one at a time) and collected answers before moving on.
  
### DIAGNOSIS & NEXT STEPS
- Once you have gathered sufficient information from follow-up Q&A for the relevant symptoms:
  - Provide a possible diagnosis by calling `diagnose_condition`.
  - Ask the user whether they want an explanation of the diagnosis (use `explain_diagnosis` if they request it).
  - Ask the user whether they want treatment recommendations (use `recommend_treatment` if they request it).

### QUESTION FLOW RULES
- Always ask **one** question at a time and wait for the user's response.
- Never skip or omit any follow-up question generated from relevant retrieved documents.
- If the user supplies only a single symptom (e.g., "I have a headache"), repeatedly ask:
    "Are you experiencing any other symptoms?" until they reply "no" / "no more symptoms".
- If the user supplies multiple symptoms in one message, still ask:
    "Are you experiencing any other symptoms?" and continue asking until they say "no" / "no more symptoms".
- Only after the user confirms they are done listing symptoms, proceed with the sequential retrieve/check_documents flow described above.

### TOOL USAGE (example pseudo-calls)
- After user finishes listing symptoms:
  For symptom in symptoms_in_order:
    - retrieved_docs = retrieve(medical_term)
    - check_result = check_documents(retrieved_docs)
    - if check_result == "relevant":
         - followup_questions = generate_questions_from(retrieved_docs)
         - ask each question one at a time, waiting for answers
      else:
         - add symptom to no-info list

### Example Interaction - Single Symptom
User: "I have a pain in the head"
Assistant: "Are you experiencing any other symptoms?"
User: "No."
Assistant:
  - Rewrite "pain in the head" → "headache"
  - Call: retrieve("headache")
  - Call: check_documents(retrieved_docs_for_cephalgia)
  - If relevant → generate follow-up Qs from docs and ask them one-by-one
  - If not relevant → tell user "I don't have information about this symptom: headache."

### Example Interaction - Multiple Symptoms (shows sequential retrieve & checks and asking for more symptoms)
User: "I have pain in the chest and shortness of breath."
Assistant: "Are you experiencing any other symptoms?"
User: "Yes, dizziness."
Assistant: "Are you experiencing any other symptoms?"
User: "No."
Assistant (processing starts now, in order provided):
  1) Rewrite "pain in the chest" → "chest pain"
     - Call: retrieve("chest pain")
     - Call: check_documents(retrieved_docs_for_chest_pain)
     - If relevant → generate ALL follow-up Qs for chest pain from those documents; ask them one at a time, wait for answers before next question.
     - If not relevant → add "chest pain" to no-info list (do not ask follow-ups for it).
  2) Rewrite "shortness of breath" → "dyspnea"
     - Call: retrieve("dyspnea")
     - Call: check_documents(retrieved_docs_for_dyspnea)
     - If relevant → generate ALL follow-up Qs for dyspnea; ask them one at a time.
     - If not relevant → add "shortness of breath" to no-info list.
  3) Rewrite "dizziness" → "dizziness"
     - Call: retrieve("dizziness")
     - Call: check_documents(retrieved_docs_for_dizziness)
     - If relevant → generate ALL follow-up Qs for dizziness; ask them one at a time.
     - If not relevant → add "dizziness" to no-info list.
Assistant: After processing all symptoms, say:
  - "I don't have information about these symptoms: [list]" (if any)
  - Continue only with symptoms for which relevant documents were found and for which follow-up Q&A was completed.


### FINAL CONTEXT
Here is the user profile information (it may be empty): {formatted_memory}
Summary of the conversation so far (it may be empty): {summary}
"""


    user_id = config["configurable"]["user_id"]
    namespace_for_memory = ("user_profile", user_id)
    user_profile = store.get(namespace_for_memory, "user_details")
    formatted_memory = None
    if user_profile and user_profile.value:
        memory_dict = user_profile.value
        formatted_memory = (
            f"Name: {memory_dict.get('user_name', 'Unknown')}\n"
            f"Known Medical Conditions: {', '.join(memory_dict.get('conditions', []))}"
            f"Age: {memory_dict.get('age', 'Unknown')}\n"
            f"Gender: {memory_dict.get('gender', 'Unknown')}\n"
        )
    else:
        formatted_memory = None
    
    system_message = None
    if summary:
        system_message = SystemMessage(
            content=prompt.format(formatted_memory=formatted_memory, summary=summary)
        )
    else:
        system_message = SystemMessage(
            content=prompt.format(formatted_memory=formatted_memory, summary="")
        )
    messages = [system_message] + state["messages"]
    response = llm_with_tool.invoke(messages)
    return {"messages": response}