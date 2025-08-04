from langchain_core.tools import tool
from typing import List, Dict
from app.model.chatmodel import llm



@tool
def recommend_treatment(diagnosis:str, user_profile:str) -> str:
    """
    Provide lifestyle or medical advice based on the user's diagnosis and profile.

    Args:
        diagnosis (str): 
            A string describing the user's diagnosis.

        user_profile (str):
            A string containing the user's profile information, which include age, gender, and medical conditions.

    Returns:
        str: 
            A string containing the recommended lifestyle changes or medical advice.
    """
    prompt = f"""
    You are an experienced medical assistant.
    Based on the following diagnosis and user profile, provide appropriate lifestyle changes or medical advice.
    Be concise and medically sound. Always provide advice based on the diagnosis and user profile.

    Diagnosis:
    {diagnosis}

    User Profile:
    {user_profile}

    Recommendations:
    """

    response = llm.invoke(prompt)
    return response 

