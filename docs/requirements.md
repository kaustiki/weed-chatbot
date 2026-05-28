# Weed Management Chatbot Requirements

## Project Goal

Build a question-answering application that helps farmers ask questions about weeds found in their fields. The app should answer using information from the provided dataset:

- `NoxWeedMangementGuide2019LasAnimas.pdf`

The system should retrieve relevant information from the PDF and provide practical answers about weed identification, lifecycle, growth stage, and control methods.

## Source Assignment Summary

The assignment describes a farmer-facing weed assistance tool. Farmers may misidentify noxious weeds because invasive species can share similar traits, such as purple flower heads, rosettes, spines, or similar growth habits.

The app should support questions such as:

- "I have a weed with purple flower heads, nodding, spine-tipped bracts, and a rosette present last fall. Which thistle is this?"
- "What is the correct timing window for treating diffuse knapweed at the rosette stage?"
- "How should saltcedar be controlled if mowing is ineffective?"

## Functional Requirements

### 1. PDF Reading

The application must be able to read the provided weed management PDF.

Requirements:

- Load the PDF from the local project directory.
- Extract readable text from each page.
- Preserve useful metadata, such as page number and source filename.
- Handle PDF extraction errors gracefully.
- Keep the original PDF as the source of truth for the chatbot's answers.

Recommended library:

- `PyMuPDF` / `pymupdf`

Reason:

- The weed management guide includes structured pages and herbicide tables.
- PyMuPDF gives better page layout handling than basic text-only PDF extraction.
- The project can still compare output against `pypdf` or `pdfplumber` if table extraction quality becomes a problem.

### 2. Data Chunking

The extracted PDF text must be split into smaller searchable chunks.

Requirements:

- Split text into chunks small enough for embedding and retrieval.
- Keep related information together when possible, especially weed name, identification keys, lifecycle, growth form, and control methods.
- Use overlap between chunks so important context is not lost between chunk boundaries.
- Store chunk metadata, including page number, source file, and chunk index.

Suggested chunk settings:

- Chunk size: 500 to 1,000 words or equivalent characters.
- Chunk overlap: 75 to 150 words or equivalent characters.

### 3. Data Storage

The application must store processed chunks so they can be searched efficiently.

Requirements:

- Convert chunks into embeddings using OpenAI `text-embedding-3-small`.
- Store embeddings in ChromaDB.
- Store the original text with each embedding.
- Store metadata with each chunk for source citation.
- Rebuild the index when the PDF or chunking logic changes.

Recommended storage:

- ChromaDB local vector database

ChromaDB should store:

- Document text
- Embedding vector
- Chunk ID
- Source metadata, such as source PDF, page number, weed name, and section

Example metadata:

```python
{
    "source": "NoxWeedMangementGuide2019LasAnimas.pdf",
    "page": 2,
    "weed_name": "Musk thistle",
    "section": "identification"
}
```

FAISS can also be used for vector search, but it is primarily a vector index. It does not store document text and rich metadata as directly as ChromaDB, so metadata would need to be managed in a separate store.

### 4. Question Answering

The application must answer user questions using retrieved context from the PDF.

Requirements:

- Accept natural-language questions from a farmer or field user.
- Retrieve the most relevant chunks from the PDF dataset.
- Generate an answer grounded in the retrieved chunks.
- Include practical details when available:
  - Candidate weed species
  - Identification keys
  - Lifecycle
  - Growth form or growth stage
  - Mechanical control
  - Cultural control
  - Biological control
  - Chemical control
  - Recommended treatment timing
- Avoid inventing facts that are not supported by the PDF.
- If the answer is not found in the PDF, say that the dataset does not contain enough information.
- Include the source page or document reference when possible.

Recommended LLM:

- OpenAI chat model for final answer generation.

Recommended answer flow:

1. Embed the user's question.
2. Search ChromaDB for the most relevant chunks.
3. Pass retrieved chunks to the LLM as context.
4. Ask the LLM to answer only from the provided context.
5. Return answer plus source metadata.

### 5. Farmer-Facing UI

The app must provide a simple interface for asking weed-related questions.

Requirements:

- Provide a text input for the farmer's question.
- Show the generated answer clearly.
- Show retrieved source snippets or citations.
- Support questions about observed plant characteristics.
- Support questions about weed control timing and methods.

Possible UI choices:

- Jupyter notebook demo
- Streamlit app
- Gradio app
- Simple command-line demo

### 6. Backend Retrieval

The backend must retrieve information relevant to the user's question.

The retrieval system should support:

- Candidate species based on identification keys.
- Lifecycle and growth-stage details.
- Recommended control methods.
- Herbicide timing and application guidance when present in the PDF.
- Questions comparing similar weeds, such as bull thistle, musk thistle, Canada thistle, and Scotch thistle.

## Learning Requirements

The project should demonstrate understanding of the following topics.

### How to Read PDF Files

The final solution should show how the PDF is loaded and how text is extracted from it. The implementation should explain or demonstrate why PDF text extraction can be imperfect and why extracted text should be inspected before building the chatbot.

### How to Chunk the Data

The final solution should show how long PDF text is divided into chunks. The chunking method should be selected to keep weed-specific information together as much as possible.

### How to Store the Data

The final solution should show how extracted chunks are stored for retrieval. If embeddings are used, the solution should explain how chunks are converted into vectors and saved in a searchable vector index.

### How to Build the Question-Answering Application

The final solution should include the full flow:

1. Read PDF.
2. Extract text.
3. Chunk text.
4. Create embeddings with OpenAI `text-embedding-3-small`.
5. Store documents, embeddings, and metadata in ChromaDB.
6. Accept user question.
7. Retrieve relevant chunks from ChromaDB.
8. Generate a grounded answer with an OpenAI LLM.
9. Return answer with source context.

### How to Evaluate the Final Application

The final solution should include an evaluation section that checks whether the chatbot answers correctly and stays grounded in the dataset. Use Braintrust to track and compare evaluation results.

## Evaluation Requirements

The app should be evaluated with a small test set of weed questions. Braintrust should be used to organize test cases, run evaluations, and compare output quality across changes.

Evaluation should check:

- Retrieval relevance: Did the system retrieve the right weed entry or control section?
- Answer correctness: Did the answer match the PDF?
- Grounding: Did the answer avoid unsupported claims?
- Completeness: Did the answer include identification, lifecycle, control method, or timing details when needed?
- Usability: Is the answer understandable for a farmer?
- Source traceability: Can the user see which document or page supported the answer?

Braintrust evaluation should include:

- Test input question
- Expected answer or expected facts
- Retrieved chunks
- Final generated answer
- Scores for correctness, groundedness, retrieval quality, and source citation quality

Suggested test questions:

- Which thistle has purple flower heads that are usually nodding and broad spine-tipped bracts?
- What is the lifecycle of bull thistle?
- How should Canada thistle be controlled mechanically?
- When should herbicide be applied to musk thistle?
- What are the main categories of weed control methods?
- What should the app say if the PDF does not contain an answer?

## Non-Functional Requirements

- The app should be easy to run locally.
- The app should use environment variables for secrets such as API keys.
- The app should not expose the `.env` file or API keys.
- The app should provide clear error messages when the PDF, vector index, or API key is missing.
- The app should be modular enough to separate PDF loading, chunking, storage, retrieval, and answer generation.
- The app should be reproducible using the project dependency files.

## Recommended Python Dependencies

Recommended packages for the project:

- `jupyter`
- `ipykernel`
- `pandas`
- `numpy`
- `pymupdf`
- `python-dotenv`
- `openai`
- `chromadb`
- `tiktoken`
- `braintrust`
- `autoevals`

Optional packages:

- `pypdf`
- `pdfplumber`
- `streamlit`
- `gradio`
- `langchain`
- `langchain-openai`
- `langchain-community`
- `faiss-cpu`

## Expected Deliverables

The final submission should include:

- Executable codebase.
- Demo of the weed question-answering system.
- High-level solution overview.
- PDF reading and text extraction code.
- Chunking code.
- Vector storage or retrieval implementation.
- Question-answering interface.
- Evaluation examples and results.
- Documentation explaining how to run the project.

## Success Criteria

The project is successful if a user can ask a field weed question and receive a useful, source-grounded answer from the provided PDF dataset.

The answer should help the user understand:

- Which weed species may match the observed characteristics.
- What identification features support that match.
- What lifecycle or growth stage is relevant.
- What control methods are recommended.
- When treatment should be applied, if the PDF provides timing information.
