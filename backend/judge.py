import json
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from backend.rag import retrieve_documents, create_context


def format_sources(documents):
    return [
        {
            "source": doc.metadata["source"],
            "page": doc.metadata["page"],
            "column": doc.metadata["column"],
            "topic": doc.metadata["topic"],
        }
        for doc in documents
    ]


def build_judge_inputs(payload):
    documents = retrieve_documents(payload["question"], n_results=3)

    return {
        "question": payload["question"],
        "answer": payload["answer"],
        "sources": json.dumps(format_sources(documents), indent=2),
        "source_context": create_context(documents),
    }


class JudgeResponse(BaseModel):
    retrieval_relevance: int = Field(ge=1, le=5, description="How relevant the returned sources are")
    groundedness: int = Field(ge=1, le=5, description="Whether the answer is supported by the source context")
    correctness: int = Field(ge=1, le=5, description="Whether the answer is factually correct according to the source context")
    completeness: int = Field(ge=1, le=5, description="Whether the answer covers the important details needed")
    citation_quality: int = Field(ge=1, le=5, description="Whether cited sources are appropriate and specific")
    pass_eval: bool = Field(description="True if the answer is acceptable overall")
    reason: str = Field(description="Brief explanation of the scores")


JUDGE_SYSTEM_PROMPT = """
You are an expert evaluator for a PDF-grounded weed management chatbot.

Evaluate the chatbot answer using only the provided source context. Do not use outside knowledge.

Analyze the answer across these dimensions:

1. RETRIEVAL_RELEVANCE:
   Determine whether the retrieved source context is relevant to the farmer's question.
   - 5: The context directly answers the question.
   - 3: The context is partially related but incomplete.
   - 1: The context is unrelated.

2. GROUNDEDNESS:
   Determine whether the chatbot answer is supported by the source context.
   - 5: Every important claim is supported by the context.
   - 3: Some claims are supported, but some are vague or weakly supported.
   - 1: The answer includes unsupported or invented claims.

3. CORRECTNESS:
   Determine whether the answer is factually correct according to the source context.
   - 5: The answer is correct according to the context.
   - 3: The answer is partially correct but has minor errors or omissions.
   - 1: The answer contradicts the context.

4. COMPLETENESS:
   Determine whether the answer includes the important practical details available in the context.
   Consider identification clues, lifecycle, growth form, mechanical control, biological control,
   chemical control, herbicide rates, and herbicide timing when available.

5. CITATION_QUALITY:
   Determine whether the returned sources are specific and appropriate.
   - 5: Sources clearly support the answer.
   - 3: Sources are somewhat relevant but incomplete or too broad.
   - 1: Sources do not support the answer.

Special rule for out-of-scope questions:
If the source context does not answer the question and the chatbot says the PDF does not provide enough information,
score groundedness and correctness highly.

Your output MUST conform exactly to the JudgeResponse schema.
Do not include any text outside the structured output.
"""

JUDGE_USER_PROMPT = """
Evaluate this chatbot response.

<question>
{question}
</question>

<chatbot_answer>
{answer}
</chatbot_answer>

<returned_sources>
{sources}
</returned_sources>

<source_context>
{source_context}
</source_context>
"""

JUDGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", JUDGE_SYSTEM_PROMPT),
        ("human", JUDGE_USER_PROMPT),
    ]
)

judge_llm = ChatOpenAI(
    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

judge_chain = (
    RunnableLambda(build_judge_inputs)
    | JUDGE_PROMPT
    | judge_llm.with_structured_output(JudgeResponse)
)
