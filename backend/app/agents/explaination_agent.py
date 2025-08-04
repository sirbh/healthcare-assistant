from langchain_core.tools import tool
from typing import List, Dict
from app.model.chatmodel import llm



@tool
def explain_diagnosis(diagnosis:str, symptoms: List[str], follow_up_qna: List[Dict[str, str]], user_profile:str) -> str:
    """
    Provide an explanation of the user's diagnosis based on their profile.

    Args:
        diagnosis (str): 
            A string describing the user's diagnosis.
        symptoms (List[str]):
            A list of symptoms reported by the user.
        follow_up_qna (List[Dict[str, str]]): 
            A list of follow-up questions and corresponding answers.
            Each item in the list must be a dictionary with the following keys:
                - 'question': The follow-up question asked (e.g., "When did the symptoms start?").
                - 'answer': The user's answer to that question (e.g., "Two days ago.").
        user_profile (str):
            A string containing the user's profile information, which include age,
            gender, and medical conditions.
    Returns:
        str: 
            A string containing the explanation of the diagnosis.
    """
    formatted_qna = "\n".join(
        f"Q: {item['question']}\nA: {item['answer']}" for item in follow_up_qna
    )

    prompt = f"""
    You are an experienced medical assistant.
    Based on the following diagnosis, symptoms, follow-up questions, and user profile, provide a clear explanation of the diagnosis.
    Be concise and medically sound. Always provide explanations based on the diagnosis, symptoms, follow-up questions, and user profile.

    Diagnosis:
    {diagnosis}

    Symptoms:
    {', '.join(symptoms)}

    Follow-up Questions and Answers:
    {formatted_qna}

    User Profile:
    {user_profile}

    Explanation:
    """

    response = llm.invoke(prompt)
    return response