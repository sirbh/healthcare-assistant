from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from enum import Enum
from app.store.data import get_vector_store
from langchain.tools.retriever import create_retriever_tool
from dotenv import load_dotenv
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from typing import List, Dict
from langgraph.types import interrupt
from langgraph.store.base import BaseStore
from langchain_core.runnables.config import RunnableConfig
from PIL import Image
from trustcall import create_extractor


import io


from langchain.schema import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import RemoveMessage 

from langgraph.types import Command, interrupt

load_dotenv(override=True)

# LangChain chat model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

vector_store = get_vector_store()

class QA(BaseModel):
    question: str
    answer: str


    
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

trustcall_extractor = create_extractor(
    llm,
    tools=[UserProfile],
    tool_choice="UserProfile"
)

def write_memory(state: MessagesState, config: RunnableConfig, store: BaseStore):

    """Reflect on the chat history and save a memory to the store."""

    
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    namespace_for_memory = ("user_profile", user_id)
    user_profile = store.get(namespace_for_memory, "user_details")

    existing_profile = {"UserProfile": user_profile.value} 
    formatted_memory = None
    if user_profile and user_profile.value:
        memory_dict = user_profile.value
        formatted_memory = (
            f"Name: {memory_dict.get('user_name', 'Unknown')}\n"
            f"Known Medical Conditions: {', '.join(memory_dict.get('known_medical_conditions', []))}"
            f"Age: {memory_dict.get('age', 'Unknown')}\n"
            f"Gender: {memory_dict.get('gender', 'Unknown')}\n"
        )
    else:
        formatted_memory = None

    system_msg = """Update the user profile (JSON doc) to incorporate new information from the following conversation: {messages}
                 Always use facts provided by the user not by the AI
                 Don't predict anything about the user
                 This is I already know about the user: {memory}
                 If you find any new information about the user, update the user profile.
                 Make sure conditions should be a list of medical conditions the user share and you should rewrite them in proper medical terms.
                 """

    result = trustcall_extractor.invoke({"messages": [SystemMessage(content=system_msg.format(messages=state['messages'], memory=formatted_memory))]}, 
                                 {"existing": existing_profile })
    updated_schema = result["responses"][0].model_dump_json()

    store.put(namespace_for_memory, "user_details", updated_schema)


@tool(response_format="content_and_artifact")
def retrieve(symptom: str):
    """
    Retrieve follow up quetion based on user input.

    Args:
        symptom (str): A normalized or rewritten symptom query (e.g., 'fever', 'headache').
                       This should be a concise medical term rather than a free-form user input.
    """

    
    retrieved_docs = vector_store.similarity_search(symptom, k=1)
    serialized = "\n\n".join(
        (f"Symtom: {doc.page_content}\nMore_Details_About_Symptom: {doc.metadata}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

@tool
def check_documents(symptoms: List[str], documents: List[str]) -> str:
    """
    Check that if retrieved documents are relevant  based on the user's symptoms.

    Args:
        symptoms (List[str]): A list of user-reported symptoms.
        documents (List[str]): A list of retrieved documents containing information about the symptoms.

    Returns:
        str: yes or no .
    """

    prompt = """
    You are a medical assistant. Based on the following symptoms and retrieved documents, determine if the documents are relevant to the symptoms.
    If they are relevant answer documents are relevant to the symptoms
    If they are not relevant answer documents are not relevant to the symptoms.
    No other answers are allowed.
    Symptoms: {symptoms}
    Documents: {documents}
    """

    response = llm.invoke(prompt.format(symptoms=symptoms, documents=documents))
    return response

@tool
def diagnose_condition(symptoms: List[str], follow_up_qna: List[Dict[str, str]]) -> str:
    """
    Provide a possible diagnosis based on symptoms and follow-up Q&A.

    Args:
        symptoms (List[str]): A list of user-reported symptoms.
        follow_up_qna (List[Dict[str, str]]): A list of Q&A dictionaries with 'question' and 'answer' keys.

    Returns:
        str: A diagnosis or 'Unable to determine' if insufficient information.
    """
    formatted_qna = "\n".join(
        f"Q: {item['question']}\nA: {item['answer']}" for item in follow_up_qna
    )

    prompt = f"""
    You are an experienced medical assistant.
    Based on the following symptoms and follow-up Q&A, provide a likely diagnosis.
    Be concise and medically sound.

    Symptoms:
    {', '.join(symptoms)}

    Follow-up Q&A:
    {formatted_qna}

    Diagnosis:
    """

    response = llm.invoke(prompt)
    return response

@tool
def explain_diagnosis(diagnosis: str, symptoms: List[str], follow_up_qna: List[Dict[str, str]]) -> str:
    """
    Provide a reasoning-based explanation for a given diagnosis using symptoms and follow-up Q&A.

    Args:
        diagnosis (str): The diagnosed condition.
        symptoms (List[str]): List of user-reported symptoms.
        follow_up_qna (List[Dict[str, str]]): Follow-up questions and answers, each as a dict with 'question' and 'answer'.

    Returns:
        str: A natural language explanation justifying the diagnosis.
    """

    formatted_qna = "\n".join(
        f"Q: {item['question']}\nA: {item['answer']}" for item in follow_up_qna
    )

    prompt = f"""
    You are a helpful and knowledgeable medical assistant.
    Given the following diagnosis, symptoms, and follow-up Q&A, explain why this diagnosis was made.
    Justify the reasoning with reference to the relevant symptoms and answers.

    Diagnosis:
    {diagnosis}

    Symptoms:
    {', '.join(symptoms)}

    Follow-up Q&A:
    {formatted_qna}

    Explanation:
    """

    response = llm.invoke(prompt)
    return response


llm_with_tool = llm.bind_tools([retrieve, check_documents, diagnose_condition, explain_diagnosis])

tools = ToolNode([retrieve, check_documents, diagnose_condition])



class ResponseFormatter(BaseModel):
    """Always use this tool to structure your response to the user."""
    chat_name: str = Field(description="The name of the chat, based on the user's input.")

class GeneratorFormatter(BaseModel):
    """Always use this tool to structure your response to the user."""

    followup_questions: List[str] = Field(
        description="A list of follow-up questions to ask the user based on their symptom or input."
    )

llm_with_struct = llm.with_structured_output(ResponseFormatter)



# Graph definition
def call_model(state: ExtendedMessagesState,config: RunnableConfig, store: BaseStore):

    summary = state.get("summary", "")

    prompt = """You are a medical assistant specialized in understanding user-described symptoms. \
                Ask for user symptoms continuously until user says no more symptoms. \
                Once you have the information, retrieve relevant follow-up questions based on the user's input. \
                Use the retrieve tool to get the most relevant information. \
                While retrieving information rewrite user symptoms to proper medical terminology so that retrieval is more effective. \
                Always check the retrieved documents with the check_documents tool to ensure they are relevant to the user's symptoms. \
                If the documents are not relevant, tell user these I have no knowledge about these symptoms. \
                If the documents are relevant, use the information to generate follow-up questions. \
                Then ask the user follow-up questions based on the retrieved information. \
                Ask one question at a time and wait for the user's response. \
                Once you have enough information, provide a possible diagnosis using the diagnose_condition tool. \
                You can also ask you if they want explanation of the diagnosis and you can use explain_diagnosis tool. \
                Here is the user profile information(it may be empty): {formatted_memory}
                Summary of the conversation so far(it may be empty): {summary}"""

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


def summarize_conversation(state: ExtendedMessagesState):
    
    # First, we get any existing summary
    summary = state.get("summary", "")

    # Create our summarization prompt 
    if summary:
        
        # A summary already exists
        summary_message = (
            f"This is summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
            " Keep the summary concise and relevant to the conversation.\n\n"
            "Use max 200 words for the summary.\n\n"
        )
        
    else:
        summary_message = "Create a summary of the conversation above using max 200 words:"

    # Add prompt to our history
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = llm.invoke(messages)
    
    # Delete all but the 2 most recent messages
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}

def should_continue(state: ExtendedMessagesState):
    
    """Return the next node to execute."""

    
    messages = state["messages"]



    # If there are more than 40 messages, then we summarize the conversation
    if len(messages) > 40:
        return "summarize_conversation"
    
    # Otherwise we can just end
    return "assistant"





def create_graph(store, checkpointer):
    builder = StateGraph(MessagesState)
    builder.add_node("assistant", call_model)
    builder.add_node("tools", tools)
    builder.add_node("summarize_conversation", summarize_conversation)
    builder.add_node("write_memory", write_memory)


    # builder.add_edge(START, "assistant")
    # builder.add_conditional_edges(
    #     "assistant",
    #     tools_condition,
    #     {END: END, "tools": "tools"},
    # )
    # builder.add_edge("tools", "assistant")

    builder.add_conditional_edges(
        START,
        should_continue,
        {
            "summarize_conversation": "summarize_conversation",
            "assistant": "assistant",
        },
    )
    builder.add_edge("summarize_conversation", "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
        {
            END: "write_memory",
            "tools": "tools",
        } 
    )

    builder.add_edge("tools", "assistant")
    builder.add_edge("write_memory", END)


    anotherb =  builder.compile(store=store, checkpointer=checkpointer)
    # png_bytes = anotherb.get_graph().draw_mermaid_png()
    # image = Image.open(io.BytesIO(png_bytes))

# Show image using default image viewer
    # image.show()

    return anotherb









