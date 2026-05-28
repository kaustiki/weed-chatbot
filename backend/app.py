from fastapi import FastAPI
from pydantic import BaseModel, Field

from backend.rag import answer_question


app = FastAPI(
    title="Weed Management Chatbot API",
    description="API for answering weed management questions using PDF-grounded RAG.",
    version="0.1.0",
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "Weed Management Chatbot API is running.",
    }


@app.post("/ask")
def ask_question(request: AskRequest):
    return answer_question(request.question)