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

    prompt = """You are a medical assistant specialized in understanding user-described symptoms. \
                If user ask non-medical questions, politely tell them to ask about their symptoms. \
                Ask for user symptoms continuously until user says no more symptoms. \
                Once you have the information, retrieve relevant follow-up questions based on the user's input. \
                Use the retrieve tool to get the most relevant information. \
                While retrieving information rewrite user symptoms to proper medical terminology so that retrieval is more effective. \
                Always check the retrieved documents with the check_documents tool to ensure they are relevant to the user's symptoms. \
                If the documents are not relevant, tell user these I have no knowledge about these symptoms. \
                If the documents are relevant, use the information to generate follow-up questions. \
                Then ask user all the follow-up questions based on the retrieved information. \
                Ask one question at a time and wait for the user's response. \
                Once you have enough information, provide a possible diagnosis using the diagnose_condition tool. \
                You can also ask you if they want explanation of the diagnosis and you can use explain_diagnosis tool. \
                You can alos ask if they want treatment recommendations and you can use recommend_treatment tool. \
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