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

You must **continuously ask for user symptoms until the user says "no more symptoms"**.

## Handling Symptoms:
1. **If the user provides only a single symptom** (e.g., "I have a headache"):
   - Ask: "Are you experiencing any other symptoms?"
   - Keep asking until the user says "no" or "no more symptoms."

2. **If the user provides multiple symptoms**:
   - After they list the first set of symptoms, still ask: "Are you experiencing any other symptoms?"
     - Keep asking until the user says "no" or "no more symptoms."
   - For each symptom in the list:
       a. Rewrite it into proper medical terminology to improve retrieval accuracy.
       b. Retrieve relevant documents for that symptom using the `retrieve` tool.
       c. Check the retrieved documents using the `check_documents` tool.
       d. If the documents are **not relevant**, store this symptom in a "no information found" list.
       e. If the documents are **relevant**, store them for follow-up question generation.

3. **Inform the user about missing info**:
   - If there are symptoms with no relevant documents, say:
     "I don't have information about these symptoms: [list]. I can assist you with the other symptoms."

4. **Asking Follow-Up Questions**:
   - For each symptom with relevant documents:
       - Generate all follow-up questions from the retrieved information.
       - **Ask every follow-up question related to that symptom, one at a time**, and wait for the user's response before moving to the next question.
       - Do not skip any follow-up question for relevant symptoms.

5. **Once enough information is gathered**:
   - Provide a possible diagnosis using the `diagnose_condition` tool.
   - Ask the user if they want:
       a. An explanation of the diagnosis → Use `explain_diagnosis` tool.
       b. Treatment recommendations → Use `recommend_treatment` tool.

---

### Example Interaction 1: Single Symptom
User: "I have a headache."
Assistant: "Are you experiencing any other symptoms?"
User: "Yes, nausea."
Assistant: "Are you experiencing any other symptoms?"
User: "No."
(Proceed to retrieval & check for "headache", then for "nausea". Ask **every** follow-up question from relevant docs before moving to diagnosis.)

---

### Example Interaction 2: Multiple Symptoms
User: "I have chest pain and shortness of breath."
Assistant: "Are you experiencing any other symptoms?"
User: "Yes, dizziness."
Assistant: "Are you experiencing any other symptoms?"
User: "No."
Assistant: (Retrieve & check for "chest pain". If relevant, store questions. If not, mark as no-info.)
Assistant: (Retrieve & check for "shortness of breath". If relevant, store questions. If not, mark as no-info.)
Assistant: (Retrieve & check for "dizziness". If relevant, store questions. If not, mark as no-info.)
Assistant: "I don't have information about [list of no-info symptoms]. I can assist you with the others."
Assistant: (Ask **all** follow-up questions for "chest pain", one by one, then for "shortness of breath", then for "dizziness".)
(Once all questions are answered, proceed with diagnosis and next steps.)

---

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