from langchain_core.tools import tool
from typing import List, Dict
from app.model.chatmodel import llm



@tool
def diagnose_condition(symptoms: List[str], follow_up_qna: List[Dict[str, str]], user_profile:str) -> str:
    """
    Provide a possible diagnosis based on user-reported symptoms and follow-up question-answer pairs.

    Args:
        symptoms (List[str]): 
            A list of symptoms reported by the user.

        follow_up_qna (List[Dict[str, str]]): 
            A list of follow-up questions and corresponding answers. 
            Each item in the list must be a dictionary with the following keys:
                - 'question': The follow-up question asked (e.g., "When did the symptoms start?").
                - 'answer': The user's answer to that question (e.g., "Two days ago.").

            Example:
            [
                {"question": "When did the symptoms start?", "answer": "Two days ago."},
                {"question": "Have you taken any medication?", "answer": "Only paracetamol."}
            ]
        user_profile (str):
            A string containing the user's profile information, which include age, gender, and medical conditions.

    Returns:
        str: 
            A string describing the possible diagnosis based on the given input.
    """
    formatted_qna = "\n".join(
        f"Q: {item['question']}\nA: {item['answer']}" for item in follow_up_qna
    )

    prompt = f"""
    You are an experienced medical assistant.
    Based on the following symptoms, user profile, and follow-up Q&A, provide a likely diagnosis.
    Be concise and medically sound. Always provide a diagnosis based on the symptoms and user profile.

    Symptoms:
    {', '.join(symptoms)}

    Follow-up Q&A:
    {formatted_qna}

    User Profile:
    {user_profile}

    Diagnosis:
    """

    response = llm.invoke(prompt)
    return response