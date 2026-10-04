from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.rag import answer_question
import os

try:
    from braintrust import init_logger, traced
except ImportError:
    init_logger = None
    traced = None


braintrust_logger = None

if init_logger and os.getenv("BRAINTRUST_API_KEY"):
    braintrust_logger = init_logger(project="weed-management-chatbot-production")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_BUILD_DIR = PROJECT_ROOT / "frontend" / "build" / "client"
ENABLE_LLM_JUDGE = os.getenv("ENABLE_LLM_JUDGE", "false").lower() == "true"

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
    result = answer_question(request.question)

    judge_result = None

    if ENABLE_LLM_JUDGE:
        from backend.judge import judge_chain

        judge_response = judge_chain.invoke(
            {
                "question": request.question,
                "answer": result["answer"],
            }
        )

        judge_result = judge_response.model_dump()

    if braintrust_logger:
        braintrust_logger.log(
            input=request.question,
            output=result["answer"],
            metadata={
                "sources": result.get("sources", []),
                "judge": judge_result,
            },
        )

    return result

# Serve the built React frontend when FastAPI runs as the final single server.
# During development, the fastapi/uvicorn server runs and the the React/Vite server also runs on port 5173 and forwards `/ask` requests to this FastAPI server on port 8000.
@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_BUILD_DIR / "index.html")
