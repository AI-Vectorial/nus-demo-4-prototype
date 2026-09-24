"use client";

import { useEffect, useState } from "react";

type Health = {
  status: string;
  build: string;
  environment: string;
  dependencies: Record<string, string>;
};

export default function Chat({ apiUrl }: { apiUrl: string }) {
  const [health, setHealth] = useState<Health | null>(null);
  const [reachable, setReachable] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(`${apiUrl}/healthz`)
      .then((r) => r.json())
      .then((data: Health) => {
        setHealth(data);
        setReachable(true);
      })
      .catch(() => setReachable(false));
  }, [apiUrl]);

  return (
    <main className="wrap">
      <header>
        <h1>Policy Assistant</h1>
        <p className="lede">
          Ask a question about internal policy. Answers cite the sections they came
          from.
        </p>
      </header>

      {/* Step 1: the conversation shell exists but does not yet answer.
          Retrieval and generation arrive in step 3, built through the pipeline. */}
      <section className="chat" aria-label="Conversation">
        <div className="placeholder">
          <strong>The scaffold.</strong> The surface is here; it does not answer yet.
          The corpus is indexed and waiting, the stores are connected — retrieval,
          refusal and generation are yours to build.
          <br />
          <br />
          Read <code>docs/PRD.md</code> for what must be true, and{" "}
          <code>docs/features.md</code> for what to build first. Then open{" "}
          <code>pipeline/01-shape.md</code>.
        </div>
      </section>

      <form
        className="composer"
        onSubmit={(e) => e.preventDefault()}
        aria-label="Ask a question"
      >
        <input
          type="text"
          placeholder="What is the approval threshold for a travel expense claim?"
          disabled
          aria-label="Your question"
        />
        <button type="submit" disabled>
          Ask
        </button>
      </form>

      {/*
        Your components go here.

          <Answer />      F5 -- the composed answer and its citations
          <Refusal />     F3 -- visibly different from an answer, and from an error
          <Degraded />    F4 -- the kill switch, shown honestly

        docs/features.md has the order. Build F1-F5, deploy, then choose.
      */}

      <footer>
        {reachable === null && <span className="mono dim">checking API…</span>}
        {reachable === false && (
          <span className="mono bad">API unreachable at {apiUrl}</span>
        )}
        {reachable && health && (
          <span className="mono dim">
            api {health.status} · build {health.build} · {health.environment}
          </span>
        )}
      </footer>
    </main>
  );
}
