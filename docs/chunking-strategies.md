# Chunking Strategies for the Weed Management Chatbot

link: https://www.pinecone.io/learn/chunking-strategies/

## Purpose

Chunking means splitting a long document into smaller pieces before storing it for retrieval. For this project, the source document is `NoxWeedMangementGuide2019LasAnimas.pdf`, and the chatbot should retrieve the right weed identification and control details when a farmer asks a question.

Good chunks should be:

- Small enough to embed and search accurately.
- Large enough to make sense without needing the whole PDF.
- Structured enough to keep each weed's identification, lifecycle, and control methods together.

Reference: Pinecone's chunking guide explains that chunks should balance context, retrieval accuracy, embedding limits, and latency: https://www.pinecone.io/learn/chunking-strategies/

## Recommended Starting Strategy

Use content-aware chunking by weed entry.

The weed guide is organized around repeated sections such as:

- Weed name
- Keys to ID
- Identification
- Lifecycle
- Growth form
- Flower, leaves, stems, roots, seedling
- Control
- Herbicide, rate, and timing

For this dataset, the best first approach is to keep one weed entry together when possible. This makes retrieval better for questions like:

- "Which thistle has nodding purple flower heads?"
- "What is the lifecycle of bull thistle?"
- "When should herbicide be applied to musk thistle?"

## Practical Approach

1. Extract text from the PDF with PyMuPDF.
2. Clean obvious spacing and line-break issues.
3. Split by weed/species headings when possible.
4. If an entry is too long, split it into smaller overlapping chunks.
5. Store metadata with every chunk:
   - `source`
   - `page`
   - `chunk_id`
   - `weed_name` when detected
   - `section` when detected

## Chunk Size Recommendation

Start with:

- `chunk_size`: 800 to 1,200 tokens
- `chunk_overlap`: 100 to 200 tokens

This should preserve enough context for weed identification and treatment recommendations while avoiding chunks that are too broad.

## Strategies to Compare

### 1. Fixed-Size Chunking

Split text every fixed number of tokens or characters.

Pros:

- Simple to implement.
- Good baseline.
- Works well enough for many RAG applications.

Cons:

- Can split a weed name from its control recommendations.
- Can separate herbicide timing from the relevant species.

Use this as the baseline, not necessarily the final method.

### 2. Recursive Character Chunking

Split using separators in order, such as paragraphs, lines, spaces, and then characters.

Pros:

- Better than naive fixed-size splitting.
- Tries to preserve paragraphs and sections.
- Easy to implement with LangChain's `RecursiveCharacterTextSplitter`.

Cons:

- Still may not understand weed-entry boundaries.

This is a strong default if we use LangChain.

### 3. Document Structure-Based Chunking

Split based on meaningful document structure, such as headings, species names, and section labels.

Pros:

- Best fit for this weed guide.
- Keeps each species entry more coherent.
- Improves answers about identification and treatment timing.

Cons:

- Requires more custom parsing and cleanup.
- PDF extraction may produce imperfect headings or line breaks.

This is the recommended project strategy.

### 4. Semantic Chunking

Use embeddings to detect topic shifts and group related sentences.

Pros:

- Can create more meaning-aware chunks.
- Useful when document structure is unclear.

Cons:

- More complex.
- More expensive and slower to build.
- Probably unnecessary for this short six-page PDF.

Use only if simpler chunking performs poorly.

### 5. Chunk Expansion During Retrieval

Retrieve the top matching chunk, then include neighboring chunks before generating the final answer.

Pros:

- Helps when a retrieved chunk is missing nearby context.
- Useful for herbicide tables or section breaks.

Cons:

- Adds more text to the model context.
- Can introduce unrelated information if neighboring chunks are not from the same weed entry.

This is useful as a backup strategy.

## PDF Scraper Recommendation

For this specific PDF, start with `PyMuPDF` / `pymupdf`.

Why:

- The PDF contains structured pages and herbicide tables.
- PyMuPDF usually gives better page layout handling than basic text-only PDF extraction.
- It can extract text by page and preserve useful page-level metadata.
- It is a good first choice before deciding whether table-specific extraction is needed.

Alternatives:

- Use `pdfplumber` if herbicide tables become important and PyMuPDF output is not table-friendly enough.
- Use `pypdf` as a lightweight baseline for simple text extraction.
- Use OCR only if pages are scanned images, which this PDF does not appear to be.

## Storage and Retrieval Choice

Use ChromaDB for this demo project.

ChromaDB can store:

- The chunk text as a document.
- The embedding vector.
- Metadata such as source file, page number, weed name, and section.

Example metadata:

```python
{
    "source": "NoxWeedMangementGuide2019LasAnimas.pdf",
    "page": 2,
    "weed_name": "Musk thistle",
    "section": "identification"
}
```

FAISS can also be used for similarity search, but it does not directly manage documents and rich metadata like ChromaDB. With FAISS, metadata usually needs to be stored separately and mapped back from returned vector IDs.

## Embedding and Answer Generation

Use OpenAI `text-embedding-3-small` to create embeddings for chunks and user questions.

Use an OpenAI chat model to generate the final answer from retrieved ChromaDB chunks. The prompt should instruct the model to answer only from the retrieved PDF context and to say when the dataset does not contain enough information.

## Evaluation Plan

Use Braintrust to test multiple chunking and retrieval approaches with the same questions:

- Species identification questions.
- Lifecycle questions.
- Mechanical, biological, and chemical control questions.
- Herbicide timing questions.
- Questions where the answer is not present in the PDF.

Compare:

- Did retrieval return the right weed?
- Did the answer cite the right source chunk?
- Did the answer include the correct control timing?
- Did the answer avoid unsupported claims?

## Initial Decision

Start with PyMuPDF plus document structure-based chunking by weed entry. Store documents, embeddings, and metadata in ChromaDB. If entry detection is messy, fall back to recursive character chunking with overlap.
