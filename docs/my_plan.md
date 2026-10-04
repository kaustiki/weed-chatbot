# My Plan
1. Read PDF: use PyMuPDF (tables are there and the pdf is structured... lets first try with pymupdf as it has better page layout handling)

the pdf has 4 columns on each page... needs to be read top down.


2. Chunk text: use Document structure-based chunking

use structure-based chunking by page column, because the PDF is a 4-column brochure and each column contains one coherent topic. Most columns are weed entries, while the first page contains general weed-management information. Store simple metadata: source, page, column, and topic.
 
 Preserve metadata for source page and column number. 
{
    "source": "NoxWeedMangementGuide2019LasAnimas.pdf",
    "page": 2,
    "column": 1,
    "topic": "Bull thistle"
}


{
    "source": "NoxWeedMangementGuide2019LasAnimas.pdf",
    "page": 1,
    "column": 4,
    "topic": "Weed Control Methods"
}


3. Create embeddings: openai text embedding small (small is enough as the chunks are only 24 and data is less)

4. Store embeddings: ChromaDB (since chromadb allows us to store the document, embedding and metadata like   metadatas=[{
        "source": "NoxWeedMangementGuide2019LasAnimas.pdf",
        "page": 2,
        "topic": "Musk thistle",
        "column": 1
    }])
    FAISS can also be used but it does not store metadata like chromadb does.


5. Accept user question. and answer using llm: openai (frontend : react)


6. Evaluate the quality: BrainTrust
