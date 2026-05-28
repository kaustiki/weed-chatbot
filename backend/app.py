from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.rag import answer_question


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_BUILD_DIR = PROJECT_ROOT / "frontend" / "build" / "client"

app = FastAPI(
    title="Weed Management Q&A API",
    description="API for answering weed management questions using PDF-grounded RAG.",
    version="0.1.0",
)

if FRONTEND_BUILD_DIR.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_BUILD_DIR / "assets"),
        name="assets",
    )


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Weed Management Q&A API is running.",
    }


@app.post("/ask")
def ask_question(request: AskRequest):
    return answer_question(request.question)


@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_BUILD_DIR / "index.html")
