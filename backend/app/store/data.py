import os
import pandas as pd
import faiss
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain.schema import Document
from dotenv import load_dotenv

load_dotenv(override=True)

def parse_questions(q):
    return [x.strip() for x in str(q).split(";")]

def normalize_embeddings(embeddings):
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms

def get_vector_store():
    INDEX_FILE = "app/store/faiss_cosine_index"
    df = pd.read_csv("symptoms_data.csv")
    embeddings = OpenAIEmbeddings()

    # Convert CSV to Document list
    docs = [
        Document(
            page_content=row["symptom"],
            metadata={
                "conditions": row["conditions"],
                "follow_up_questions": parse_questions(row["follow_up_questions"])
            }
        )
        for _, row in df.iterrows()
    ]

    if os.path.exists(INDEX_FILE):
        print("🔄 Loading existing FAISS index...")
        vector_store = FAISS.load_local(INDEX_FILE, embeddings, allow_dangerous_deserialization=True)
    else:
        print("🆕 Creating FAISS index using cosine similarity...")
        dim = len(embeddings.embed_query("test"))
        index = faiss.IndexFlatIP(dim)  # Use inner product for cosine similarity

        # Patch: Wrap OpenAIEmbeddings to normalize outputs
        class NormalizedOpenAIEmbeddings(OpenAIEmbeddings):
            def embed_documents(self, texts):
                raw = super().embed_documents(texts)
                return normalize_embeddings(np.array(raw)).tolist()

            def embed_query(self, text):
                raw = super().embed_query(text)
                return (np.array(raw) / np.linalg.norm(raw)).tolist()

        normalized_embeddings = NormalizedOpenAIEmbeddings()

        vector_store = FAISS(
            embedding_function=normalized_embeddings,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={}
        )

        vector_store.add_documents(docs)
        vector_store.save_local(INDEX_FILE)
        print("💾 FAISS cosine index saved.")

    return vector_store
