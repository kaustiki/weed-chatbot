import os
from typing import List, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langgraph.graph import END, START, StateGraph

from backend.vector_store import PROJECT_ROOT, get_vector_collection


# load env variables
load_dotenv(PROJECT_ROOT / ".env")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
collection = get_vector_collection()

# 0. format responses
class Source(BaseModel):
    source: str = Field(description="Source PDF filename")
    page: int = Field(description="PDF page number")
    column: int = Field(description="Column number on the PDF page")
    topic: str = Field(description="Topic or weed name")

class RAGAnswer(BaseModel):
    answer: str = Field(description="Answer grounded in the PDF context")
    sources: List[Source] = Field(description="Sources used to answer the question")

class AnswerQuality(BaseModel):
    answer_quality: Literal["complete", "needs_more_context"]
    reasoning: str = Field(description="Explain whether coverage, specificity, or grounding is missing.")
    followup_question: str = Field(description="A better retrieval question. Empty when answer_quality is complete.")


#==================================1. Retrieve==============================
# 1. Retrieve relevant documents and context functions
def retrieve_documents(
    question: str,
    n_results: int = 2,
    exclude_chunk_ids: list[str] | None = None,
):
    # Fetch enough candidates to skip chunks gathered in earlier graph loops.
    exclude_chunk_ids = set(exclude_chunk_ids or [])
    results = collection.query(
        query_texts=[question],
        n_results=n_results + len(exclude_chunk_ids),
    )

    documents = []

    for chunk_id, text, metadata in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
    ):
        if chunk_id in exclude_chunk_ids:
            continue

        documents.append(
            Document(
                page_content=text,
                metadata={**metadata, "chunk_id": chunk_id},
            )
        )

        if len(documents) == n_results:
            break

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

#==================================2. Prompts==============================

# 2. Write prompts
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
    model=OPENAI_MODEL,
    temperature=0.2,
    api_key=os.getenv("OPENAI_API_KEY"),
)

structured_llm = llm.with_structured_output(RAGAnswer)
rag_chain = prompt | structured_llm

quality_prompt = ChatPromptTemplate.from_template(
    """
You are checking the quality of an answer from a weed-management PDF chatbot.

Use only the retrieved context. Do not use outside knowledge.

Return "complete" only when:
- the answer directly answers the visitor's question,
- it is specific and grounded in the context,
- it does not make unsupported claims,
- for weed-identification questions, the context has enough evidence to
  distinguish the identified weed from other possible similar weeds.

Return "needs_more_context" when:
- relevant details are missing,
- the answer is vague or unsupported,
- the question may need information from multiple topics,
- an identification answer needs a comparison with similar species,
- a treatment question needs missing timing or control information.

When answer_quality is "needs_more_context", write one focused
followup_question for ChromaDB retrieval.
For identification, include the visitor's observed traits and ask for
similar species or distinguishing characteristics.

Visitor question:
{visitor_question}

Topics visited:
{topics_visited}

Retrieved context:
{context}

Current answer:
{answer}
"""
)

quality_llm = llm.with_structured_output(AnswerQuality)
quality_chain = quality_prompt | quality_llm



#==================================3. Langgraph==============================
# 3. LangGraph
## 3.1 initialise state
# note: total = false make the state allow partial updates from each node: Each LangGraph node returns only the fields it changes
class WeedChatBotState(TypedDict, total=False):
    visitor_question: str
    seen_chunk_ids: list[str]
    documents_collected: list[Document]
    topics_visited: list[str]
    context: str

    answer: str
    followup_question: str
    answer_quality: Literal["complete", "needs_more_context"]
    reasoning: str

    followup_loop_count: int


## 3.2 Build langgraph nodes

def answer_question_node(state: WeedChatBotState):
    retrieved_documents = retrieve_documents(
        state.get("followup_question") or state["visitor_question"],
        n_results=2,
        exclude_chunk_ids=state.get("seen_chunk_ids", []),
    )
    documents = state.get("documents_collected", []) + retrieved_documents
    context = create_context(documents)

    response = rag_chain.invoke(
        {
            "question": state["visitor_question"],
            "context": context,
        }
    )

    return {
        "seen_chunk_ids": state.get("seen_chunk_ids", [])
        + [document.metadata["chunk_id"] for document in retrieved_documents],
        "documents_collected": documents,
        "context": context,
        "answer": response.answer,
        "topics_visited": list(
            dict.fromkeys(
                document.metadata["topic"]
                for document in documents
            )
        ),
    }

def check_answer_quality_node(state: WeedChatBotState):
    loop_count = state.get("followup_loop_count", 0)

    response = quality_chain.invoke(
        {
            "visitor_question": state["visitor_question"],
            "topics_visited": ", ".join(state.get("topics_visited", [])),
            "context": state["context"],
            "answer": state["answer"],
        }
    )

    if response.answer_quality == "needs_more_context":
        loop_count += 1

    return {
        "answer_quality": response.answer_quality,
        "reasoning": response.reasoning,
        "followup_question": response.followup_question,
        "followup_loop_count": loop_count
    }

MAX_FOLLOWUP_LOOPS = 6


def route_after_quality_check(state: WeedChatBotState):
    if state["answer_quality"] == "complete":
        return "end"

    if state.get("followup_loop_count", 0) >= MAX_FOLLOWUP_LOOPS:
        return "end"

    return "retry"

## 3.3 Build LangGraph
builder = StateGraph(WeedChatBotState)

builder.add_node("answer_question", answer_question_node)
builder.add_node("check_answer_quality", check_answer_quality_node)

builder.add_edge(START, "answer_question")
builder.add_edge("answer_question", "check_answer_quality")

builder.add_conditional_edges(
    "check_answer_quality",
    route_after_quality_check,
    {
        "end": END,
        "retry": "answer_question",
    },
)

weed_chatbot_graph = builder.compile()


#==================================4. Return answer flow==============================
def format_trace_update(update):
    """Keep document metadata in the trace; the full chunk text is in context."""
    formatted_update = update.copy()

    if "documents_collected" in formatted_update:
        formatted_update["documents_collected"] = [
            document.metadata
            for document in formatted_update["documents_collected"]
        ]

    return formatted_update


def answer_question(question: str):
    current_state = {"visitor_question": question}
    graph_trace = [
        {
            "step": 0,
            "kind": "boundary",
            "name": "START",
            "update": current_state,
        }
    ]

    for event in weed_chatbot_graph.stream(
        current_state,
        stream_mode="updates",
    ):
        for node_name, state_update in event.items():
            current_state.update(state_update)

            graph_trace.append(
                {
                    "step": len(graph_trace),
                    "kind": "node",
                    "name": node_name,
                    "update": format_trace_update(state_update),
                }
            )

            if node_name == "check_answer_quality":
                graph_trace.append(
                    {
                        "step": len(graph_trace),
                        "kind": "router",
                        "name": "route_after_quality_check",
                        "update": {
                            "next_step": route_after_quality_check(current_state),
                        },
                    }
                )

    graph_trace.append(
        {
            "step": len(graph_trace),
            "kind": "boundary",
            "name": "END",
            "update": {
                "answer_quality": current_state.get("answer_quality"),
                "followup_loop_count": current_state.get(
                    "followup_loop_count",
                    0,
                ),
            },
        }
    )

    return {
        "answer": current_state["answer"],
        "sources": [
            document.metadata
            for document in current_state.get("documents_collected", [])
        ],
        "graph_trace": graph_trace,
    }
