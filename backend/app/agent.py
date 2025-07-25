from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from app.store.data import get_vector_store
from langchain.tools.retriever import create_retriever_tool
from dotenv import load_dotenv
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from typing import List


from langchain.schema import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver

from langgraph.types import Command, interrupt

load_dotenv(override=True)

# LangChain chat model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

vector_store = get_vector_store()

class QA(BaseModel):
    question: str
    answer: str

class ExtendedMessagesState(MessagesState):
    questions: List[QA] = []


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

llm_with_tool = llm.bind_tools([retrieve])

tools = ToolNode([retrieve])



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
def call_model(state: MessagesState):
    system_instruction = SystemMessage(
        content=(
            "You are a medical assistant specialized in understanding user-described symptoms. "
            "Ask for user symptoms continuously until user says no more symptoms. "
            "Once you have the information, retrieve relevant follow-up questions based on the user's input." \
            "Use the retrieve tool to get the most relevant information. " \
            "Then ask the user follow-up questions based on the retrieved information. "\
            "Ask one question at a time and wait for the user's response. " \
        )
    )

    messages = [system_instruction] + state["messages"]
    response = llm_with_tool.invoke(messages)
    return {"messages": response}



def generate_questions(state: MessagesState):
    """Generate follow-up questions based on the retrieved content."""

    # Step 1: Collect recent tool messages (from most recent backward until the first non-tool)
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]  # Maintain original order

    # Step 2: Extract content (stringified symptom + metadata) from tool messages
    docs_content = "\n\n".join(
        message.content for message in tool_messages
    )
    
    prompt = """
           Here are the symptom and its related information:
           Get the single list of questions from the data
           Make sure quetions are not repeated
           Do not include any quetions from your side
           Here is the information: {docs_content}

    """

    response = llm.with_structured_output(GeneratorFormatter).invoke(
        prompt.format(docs_content=docs_content)
    )

    print("Generated follow-up questions:", response.followup_questions)

    questions = response.followup_questions
    qa_list = [QA(question=q, answer="") for q in questions]

    return {"questions":qa_list}

def ask_questions(state: ExtendedMessagesState):
    """Ask follow-up questions to the user until all are answered."""
    qa_list = state.get("questions", [])

    unanswered = [qa for qa in qa_list if not qa.answer.strip()]
    
    if unanswered:
        next_question = unanswered[0].question
        feedback = interrupt(next_question)

    return state


def create_graph(store, checkpointer):
    builder = StateGraph(MessagesState)
    builder.add_node("assistant", call_model)
    builder.add_node("tools", tools)


    builder.add_edge(START, "assistant")
    # builder.add_edge("assistant", END)
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    builder.add_edge("tools", "assistant")

    return builder.compile(store=store, checkpointer=checkpointer)

# def create_graph(checkpointer):
#     builder = StateGraph(ExtendedMessagesState)
#     builder.add_node("assistant", call_model)
#     builder.add_node("tools", tools)
#     builder.add_node("generate_questions", generate_questions)
    
    

#     builder.add_edge(START, "assistant")
#     # builder.add_edge("assistant", END)
#     builder.add_conditional_edges(
#         "assistant",
#         tools_condition,
#         {END: END, "tools": "tools"},
#     )
#     builder.add_edge("tools", "generate_questions")
#     builder.add_edge("generate_questions", END)

#     return builder.compile(checkpointer=checkpointer)



# def get_chat_name(message):
#     prompt="You are a medical assistant. Based on the following message, suggest a name for the chat. Use maximum 2 words.Here is the message: {message}"
#     response = llm_with_struct.invoke(prompt.format(message=message))
#     return response.chat_name



# def create_graph():
#     builder = StateGraph(MessagesState)
#     builder.add_node("assistant", call_model)
#     builder.add_node("tools", tools)
#     builder.add_node("generate_questions", generate_questions)


#     builder.add_edge(START, "assistant")
#     # builder.add_edge("assistant", END)
#     builder.add_conditional_edges(
#         "assistant",
#         tools_condition,
#         {END: END, "tools": "tools"},
#     )
#     builder.add_edge("tools", "generate_questions")
#     builder.add_edge("generate_questions", END)

#     return builder.compile()

# thread = {"configurable": {"thread_id": "1"}}
# memory = InMemorySaver()
# graph = create_graph(memory)


# while True:
#     user_input = input("You: ")
#     if user_input.lower() in ["exit", "quit"]:
#         break


#     # Invoke the graph with the current thread
#     event = graph.invoke(
#         {"messages": [HumanMessage(content=user_input)],"questions":[]},
#         config=thread,
#         )
    
#     print("Assistant:", event["messages"][-1].content)
#     print("Follow-up Questions:", event["questions"])
    


# for event in graph.stream({"messages":[HumanMessage(content="Hello")],"questions":[]}, thread, stream_mode="updates"):
#     print(event)
#     print("\n")

# result = graph.invoke({
#     "messages": [HumanMessage(content="I am feeling very tired and have a headache.")],
# })








