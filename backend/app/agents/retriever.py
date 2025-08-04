from langchain_core.tools import tool
from app.store.data import get_vector_store


vector_store = get_vector_store()

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