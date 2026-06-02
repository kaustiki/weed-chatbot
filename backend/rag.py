import os
from typing import List

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from backend.vector_store import PROJECT_ROOT, get_vector_collection


load_dotenv(PROJECT_ROOT / ".env")

collection = get_vector_collection()


class Source(BaseModel):
    source: str = Field(description="Source PDF filename")
    page: int = Field(description="PDF page number")
    column: int = Field(description="Column number on the PDF page")
    topic: str = Field(description="Topic or weed name")


class RAGAnswer(BaseModel):
    answer: str = Field(description="Answer grounded in the PDF context")
    sources: List[Source] = Field(description="Sources used to answer the question")


def retrieve_documents(question: str, n_results: int = 2):
    # Retrieve relevant chunks from ChromaDB
    results = collection.query(
        query_texts=[question],
        n_results=n_results,
    )

    documents = []

    for text, metadata in zip(results["documents"][0], results["metadatas"][0]):
        documents.append(
            Document(
                page_content=text,
                metadata=metadata,
            )
        )

    return documents


def create_context(documents):
    # Combine retrieved documents into one context block
    return "\n\n---\n\n".join(
        f"Source: {doc.metadata['source']}, "
        f"Page: {doc.metadata['page']}, "
        f"Column: {doc.metadata['column']}, "
        f"Topic: {doc.metadata['topic']}\n\n"
        f"{doc.page_content}"
        for doc in documents
    )


prompt = ChatPromptTemplate.from_template(
    """
You are a weed management assistant for farmers.

Answer the question using only the provided PDF context.

Important rules:
- If the context directly answers the question, answer clearly.
- If the context does not directly answer the question, say:
  "The PDF does not provide enough information to answer this question."
- If the context is not relevant, return an empty sources list.
- Do not guess or use outside knowledge.
- If you mention scientific names, copy them exactly from the provided context.
- Only include sources that actually support the answer.

Include practical details when available:
- identification clues
- lifecycle
- growth form
- mechanical control
- biological control
- chemical control
- herbicide timing

Context:
{context}

Question:
{question}
"""
)


llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.2,
    api_key=os.getenv("OPENAI_API_KEY"),
)

structured_llm = llm.with_structured_output(RAGAnswer)


rag_chain = prompt | structured_llm


def answer_question_with_context(question: str):
    documents = retrieve_documents(question)
    context = create_context(documents)
    response = rag_chain.invoke(
        {
            "question": question,
            "context": context,
        }
    )
    # take the structured Pydantic response object and serialize it into a regular dict.
    answer_payload = response.model_dump()

    return {
        **answer_payload,
        "retrieved_context": context,
        "retrieved_sources": [
            {
                "source": doc.metadata["source"],
                "page": doc.metadata["page"],
                "column": doc.metadata["column"],
                "topic": doc.metadata["topic"],
                "text": doc.page_content,
            }
            for doc in documents
        ],
    }


def answer_question(question: str):
    result = answer_question_with_context(question)
    return {
        "answer": result["answer"],
        "sources": result["sources"],
    }
