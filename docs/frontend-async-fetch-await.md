# Async Fetch and Await

In the frontend, `fetch()` is asynchronous because the browser sends a request to the backend and waits for a response.

```tsx
const response = await fetch("/ask", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ question }),
});
```

`await` pauses the current `async` function until the request finishes. It does not freeze the whole app. React can still update the UI while the backend is responding.

This is why the app can show other UI work during the wait, such as a submitting state:

```tsx
const isSubmitting = navigation.state === "submitting";
```

Without `await`, `fetch()` returns a Promise object:

```tsx
const response = fetch("/ask");
console.log(response);
```

Output:

```text
Promise { <pending> }
```

That means the response has not arrived yet, so this will not work correctly:

```tsx
if (!response.ok) {
  return { error: "Something went wrong." };
}
```

`response.ok` exists on the resolved HTTP response, not on the Promise.

Parsing JSON is also asynchronous:

```tsx
const data = await response.json();
```

Without `await`, `response.json()` also returns a Promise.

Short version:

```text
without await -> Promise object
with await    -> resolved result
```

For this app:

```tsx
const response = await fetch("/ask");
const data = await response.json();
```

means wait for the backend response, then wait for the JSON body, then use the final answer data.
