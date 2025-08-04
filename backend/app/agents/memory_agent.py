from langchain_core.runnables.config import RunnableConfig
from langchain.schema import SystemMessage

from trustcall import create_extractor
from langgraph.store.base import BaseStore

from .supervisor_agent import ExtendedMessagesState, UserProfile
from app.model.chatmodel import llm



trustcall_extractor = create_extractor(
    llm,
    tools=[UserProfile],
    tool_choice="UserProfile"
)

def write_memory(state: ExtendedMessagesState, config: RunnableConfig, store: BaseStore):

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

    system_msg = """Update the user profile (JSON doc) to incorporate new information from the chat history
                 Always use facts provided by the user not by the AI
                 Don't predict anything about the user
                 This is I already know about the user: {memory}
                 If you find any new information about the user, update the user profile wit new information.
                 Make sure conditions should be a list of medical conditions the user share and append it to the list provided if you found any new consition.
                 """

    result = trustcall_extractor.invoke({"messages": [SystemMessage(content=system_msg.format(memory=formatted_memory))]+ state["messages"]}, 
                                 {"existing": existing_profile })
    updated_schema = result["responses"][0].model_dump_json()

    store.put(namespace_for_memory, "user_details", updated_schema)