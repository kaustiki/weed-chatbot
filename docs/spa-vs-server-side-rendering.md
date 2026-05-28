# SPA vs Server-Side Rendering

This project uses React for the frontend and FastAPI for the backend.

In the current setup, React runs in the browser:

```text
React frontend -> browser
FastAPI backend -> server
```

The browser loads the React JavaScript, React renders the page, and then the frontend calls the backend API:

```tsx
fetch("/ask")
```

That request goes to FastAPI, which runs the RAG logic and returns the answer as JSON.

## React SPA

In a React SPA, the server sends static frontend files:

```text
HTML + CSS + JavaScript
```

Then the browser runs the JavaScript and builds the UI.

Flow:

```text
1. Browser requests the page.
2. Server sends the React app files.
3. Browser runs React.
4. React renders the Q&A interface.
5. User submits a question.
6. Browser calls FastAPI with fetch("/ask").
7. FastAPI returns JSON.
8. React displays the answer.
```

This is the best fit for the current app because the UI is simple and the backend only needs to provide the `/ask` API.

## Jinja Server-Side Rendering

Jinja templates are server-side rendering.

With Jinja, FastAPI creates the HTML on the server before sending it to the browser:

```python
templates.TemplateResponse(
    "home.html",
    {"request": request, "answer": answer},
)
```

Flow:

```text
1. Browser sends a request.
2. FastAPI runs Python code.
3. FastAPI fills a Jinja HTML template with data.
4. Server sends complete HTML to the browser.
5. Browser displays the HTML.
```

In this case, the server builds the page.

## React SSR

React server-side rendering is similar in concept to Jinja, but the server renders React components into HTML first.

Then the browser loads JavaScript and hydrates the page so it becomes interactive.

Flow:

```text
1. Server renders React to HTML.
2. Browser receives pre-rendered HTML.
3. Browser loads React JavaScript.
4. React hydrates the page.
```

## Short Version

```text
React SPA:
Server sends app files. Browser renders the UI.

Jinja SSR:
Server fills an HTML template and sends complete HTML.

React SSR:
Server pre-renders React HTML, then browser hydrates it.
```

For this project, SPA mode is enough because the frontend is a simple question-answering page and FastAPI handles the backend `/ask` API.
