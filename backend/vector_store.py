import os
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv


# Project root is one level above backend/
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Local ChromaDB folder created from the notebook
CHROMA_DB_DIR = PROJECT_ROOT / "data" / "chroma_db"

# Chroma collection name used in the notebook
COLLECTION_NAME = "weed_management_guide"

# OpenAI embedding model used in the notebook
EMBEDDING_MODEL = "text-embedding-3-small"


def get_vector_collection():
    # Load OPENAI_API_KEY from .env
    load_dotenv(PROJECT_ROOT / ".env")

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Add it to your .env file.")

    # Same embedding function used when storing chunks in ChromaDB
    embedding_function = OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=EMBEDDING_MODEL,
    )

    # Connect to the existing persistent ChromaDB directory
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    # Load the existing collection created in the notebook
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
    )

    return collection