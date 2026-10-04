// @ts-nocheck
import { Form, useActionData, useNavigation } from "react-router";

export async function clientAction({ request }) {
  const formData = await request.formData();
  const question = String(formData.get("question") ?? "").trim();

  if (!question) {
    return { error: "Please enter a question." };
  }

  const response = await fetch("/ask", {method: "POST",headers: {"Content-Type": "application/json",},body: JSON.stringify({ question })});

  if (!response.ok) {
    return { error: "Something went wrong. Please try again." };
  }

  return await response.json();
}

export default function Home() {
  const data = useActionData();
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  return (
    <main>
      <h1>Weed Management Q&A</h1>

      <Form method="post">
        <label htmlFor="question">Ask a question</label>
        <textarea
          id="question"
          name="question"
          rows={4}
          placeholder="When should herbicide be applied to musk thistle?"
        />
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Asking..." : "Ask"}
        </button>
      </Form>

      {data?.error && <p>{data.error}</p>}

      {data?.answer && (
        <section>
          <h2>Answer</h2>
          <p>{data.answer}</p>

          {data.graph_trace?.length > 0 && (
            <>
              <h2>LangGraph Trace</h2>

              <div className="graph-trace">
                {data.graph_trace.map((step) => (
                  <details key={step.step} className="graph-trace-step">
                    <summary>
                      Step {step.step}: <code>{step.name}</code> ({step.kind})
                    </summary>
                    <pre>{JSON.stringify(step.update, null, 2)}</pre>
                  </details>
                ))}
              </div>
            </>
          )}

          {data.sources?.length > 0 && (
            <>
              <h2>Sources</h2>
              <ul>
                {data.sources.map((source) => (
                  <li key={`${source.source}-${source.page}-${source.column}`}>
                    {source.topic}, page {source.page}, column {source.column}
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}
    </main>
  );
}
