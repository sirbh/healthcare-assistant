# langgraph_config.py

from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# LangChain chat model
llm = ChatOpenAI(model="gpt-4o", temperature=0)



class ResponseFormatter(BaseModel):
    """Always use this tool to structure your response to the user."""
    chat_name: str = Field(description="The name of the chat, based on the user's input.")

llm_with_struct = llm.with_structured_output(ResponseFormatter)




# Graph definition
def call_model(state: MessagesState):
    response = llm.invoke(state["messages"])
    return {"messages": response}

def create_graph(store, checkpointer):
    builder = StateGraph(MessagesState)
    builder.add_node("assistant", call_model)

    builder.add_edge(START, "assistant")
    builder.add_edge("assistant", END)

    return builder.compile(store=store, checkpointer=checkpointer)

def get_chat_name(message):
    prompt="You are a medical assistant. Based on the following message, suggest a name for the chat. Use maximum 2 words.Here is the message: {message}"
    response = llm_with_struct.invoke(prompt.format(message=message))
    return response.chat_name