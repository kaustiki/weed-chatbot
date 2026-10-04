# Running the Application

## Development Mode

Run both servers while building and testing the app.

```text
Browser -> React frontend (:5173) -> FastAPI backend (:8000) -> LangGraph, ChromaDB, and OpenAI
```

The frontend shows the user interface. The Python backend receives `/ask`
requests, runs the LangGraph workflow, and returns the answer and graph trace.

### One-Time Setup

Install the Python dependencies, including LangGraph:

```bash
uv add langgraph
```

The `.env` file needs an OpenAI API key:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

`OPENAI_API_KEY` is used for answer generation, answer-quality checks, the
optional LLM judge, and ChromaDB's embedding function. `OPENAI_MODEL` is
optional because the application defaults to `gpt-4.1-mini`.

### Terminal 1: Start the Backend

From the project root:

```bash
uv run uvicorn backend.app:app --reload --port 8000
```

Useful backend URLs:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

### Terminal 2: Start the Frontend

From the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend in a browser:

```text
http://localhost:5173
```

Vite forwards frontend `/ask` requests to the backend at
`http://localhost:8000`, as configured in `frontend/vite.config.ts`.

Do not run only the frontend: it needs the backend to answer questions.
Do not run only Python in development: the React development server provides
the latest frontend code.

## Final Single-Server Mode

For a final local deployment, build the React frontend first:

```bash
cd frontend
npm run build
```

Then return to the project root and run FastAPI:

```bash
uv run uvicorn backend.app:app --port 8000
```

Open:

```text
http://localhost:8000
```

In this mode, `backend/app.py` serves both parts:

1. The built React files from `frontend/build/client` at `/` and `/assets`.
2. The Python API at `/ask`.

## WSL Note

If `npm run dev` or `npm run build` reports that WSL 1 is unsupported, use a
supported Node.js installation or upgrade the Linux distribution to WSL 2
before running the frontend.
