from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from PIL import Image
import io

from app.agents.supervisor_agent import supervisor, ExtendedMessagesState
from app.agents.retriever import retrieve
from app.agents.evaluater_agent import check_documents
from app.agents.diagnostic_agent import diagnose_condition
from app.agents.summary_agent import summarize_conversation
from app.agents.memory_agent import write_memory

tools = ToolNode([retrieve, check_documents, diagnose_condition])


def should_continue(state: ExtendedMessagesState):
    
    """Return the next node to execute."""
    messages = state["messages"]
    # If there are more than 40 messages, then we summarize the conversation
    if len(messages) > 40:
        return "summarize_conversation" 
    # Otherwise we can just end
    return "supervisor"

def create_graph(store, checkpointer):
    builder = StateGraph(ExtendedMessagesState)
    builder.add_node("supervisor", supervisor)
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
            "supervisor": "supervisor",
        },
    )
    builder.add_edge("summarize_conversation", "supervisor")
    builder.add_conditional_edges(
        "supervisor",
        tools_condition,
        {
            END: "write_memory",
            "tools": "tools",
        } 
    )

    builder.add_edge("tools", "supervisor")
    builder.add_edge("write_memory", END)


    anotherb =  builder.compile(store=store, checkpointer=checkpointer)
    # png_bytes = anotherb.get_graph().draw_mermaid_png()
    # image = Image.open(io.BytesIO(png_bytes))

# Show image using default image viewer
    # image.show()

    return anotherb