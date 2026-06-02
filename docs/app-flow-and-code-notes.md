# App Flow and Code Notes

## Backend to Frontend Flow

1. Build the React frontend.
   - The build creates `frontend/build/client/index.html`.
   - It also creates JavaScript and CSS files inside `frontend/build/client/assets`.

2. Run the FastAPI backend.
   ```bash
   uv run fastapi dev backend/app.py
   ```

3. Open the home page.
   ```text
   http://localhost:8000/
   ```

4. FastAPI handles `/`.
   - The `/` route returns `frontend/build/client/index.html`.
   - FastAPI also mounts built frontend assets at `/assets`.

   ```python
   app.mount(
       "/assets",
       StaticFiles(directory=FRONTEND_BUILD_DIR / "assets"),
       name="assets",
   )
   ```

5. The browser loads `index.html`.
   - `index.html` loads the bundled React JavaScript from `/assets/...`.
   - React Router starts in the browser.

6. React Router renders the home route.
   - `frontend/app/routes.ts` maps `/` to `routes/home.tsx`.
   - So `home.tsx` becomes the page shown at `/`.

7. The user submits a question.
   - The form in `home.tsx` sends the input to `clientAction`.
   - `clientAction` calls the FastAPI backend at `/ask`.

8. FastAPI handles `/ask`.
   - The backend receives JSON like:

   ```json
   {
     "question": "When should herbicide be applied?"
   }
   ```

   - It calls the RAG pipeline and returns an answer as JSON.

9. React displays the result.
   - `useActionData()` receives the returned data.
   - The page displays either `data.error` or `data.answer`.

## Static Assets Path

The asset path in `index.html` must match the FastAPI mount path.

If FastAPI mounts:

```python
app.mount("/assets", StaticFiles(...))
```

then `index.html` should reference:

```html
/assets/...
```

If FastAPI mounts:

```python
app.mount("/static", StaticFiles(...))
```

then the frontend build should reference:

```html
/static/...
```

Do not manually edit built `index.html` as the main solution, because build filenames can change. Configure the frontend build path instead.

## Form Input Cleanup

```ts
const question = String(formData.get("question") ?? "").trim();
```

This means:

1. Get the value of the form field named `question`.
2. If it is `null` or `undefined`, use an empty string.
3. Convert it to a string.
4. Remove extra spaces and newlines from the start and end.

The `??` operator is called the nullish coalescing operator.

```ts
value ?? fallback
```

It uses `fallback` only when `value` is `null` or `undefined`.

## Sending JSON to FastAPI

```ts
body: JSON.stringify({ question })
```

`JSON.stringify` converts a JavaScript object into JSON text.

This object:

```ts
{ question: "When should I spray musk thistle?" }
```

becomes:

```json
{"question":"When should I spray musk thistle?"}
```

That matches the FastAPI request model:

```python
class AskRequest(BaseModel):
    question: str
```

## React Router Hooks

```ts
const data = useActionData();
const navigation = useNavigation();
const isSubmitting = navigation.state === "submitting";
```

`useActionData()` gets whatever `clientAction` returns.

Examples:

```ts
{ error: "Please enter a question." }
```

or:

```ts
{ answer: "...", sources: [...] }
```

`useNavigation()` tells the component what React Router is currently doing.

Common navigation states:

```text
idle
submitting
loading
```

For this app, the common form flow is:

```text
idle -> submitting -> idle
```

`isSubmitting` is used to disable the button and show `Asking...` while the request is running.

## Chunk Creation

The notebook turns cleaned PDF pages into smaller searchable chunks.

Flow:

```text
PDF pages -> split by column -> create chunks -> save chunks.json
```

Each chunk has:

```json
{
  "id": "page_12_column_1",
  "text": "chunk text here",
  "metadata": {
    "source": "PDF filename",
    "page": 12,
    "column": 1,
    "topic": "Musk Thistle"
  }
}
```

`extract_topic()` uses the first meaningful line of a column as the topic.

## append vs extend

`append` adds one item.

```python
items = [1, 2]
items.append([3, 4])
```

Result:

```python
[1, 2, [3, 4]]
```

`extend` adds each item from another list.

```python
items = [1, 2]
items.extend([3, 4])
```

Result:

```python
[1, 2, 3, 4]
```

In the notebook:

```python
chunks.extend(split_page_into_column_chunks(page))
```

This adds each page's column chunks into one flat `chunks` list.

## zip

```python
for text, metadata in zip(results["documents"][0], results["metadatas"][0]):
```

`zip` loops through two lists side by side.

Example:

```python
texts = ["chunk 1 text", "chunk 2 text"]
metadatas = [{"page": 1}, {"page": 2}]

for text, metadata in zip(texts, metadatas):
    print(text, metadata)
```

Output:

```text
chunk 1 text {'page': 1}
chunk 2 text {'page': 2}
```

In the RAG code, this pairs each retrieved chunk text with its matching metadata.

## LangChain Document

```python
Document(
    page_content=text,
    metadata=metadata,
)
```

In this project, a LangChain `Document` is a simple container for:

```python
doc.page_content
doc.metadata
```

The RAG flow uses it like this:

```text
question
-> retrieve_documents(question)
-> list[Document]
-> create_context(documents)
-> context string
-> LLM
```

`create_context()` reads `doc.page_content` and `doc.metadata` to build the prompt context.

## response.model_dump()

The LLM returns structured output shaped like this Pydantic model:

```python
class RAGAnswer(BaseModel):
    answer: str
    sources: List[Source]
```

So:

```python
response = rag_chain.invoke(question)
```

returns a `RAGAnswer` object.

Then:

```python
response.model_dump()
```

converts it into a normal Python dictionary:

```python
{
    "answer": "...",
    "sources": [
        {
            "source": "...",
            "page": 12,
            "column": 1,
            "topic": "..."
        }
    ]
}
```

FastAPI can then return that dictionary as JSON to the frontend.
