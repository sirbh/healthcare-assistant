from langchain_core.tools import tool
from typing import List
from app.model.chatmodel import llm

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