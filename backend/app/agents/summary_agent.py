from langchain.schema import HumanMessage
from langchain_core.messages import RemoveMessage 

from .supervisor_agent import ExtendedMessagesState
from app.model.chatmodel import llm


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
