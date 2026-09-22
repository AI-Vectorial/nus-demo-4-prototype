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
          <strong>Step&nbsp;1 scaffold.</strong> The conversation surface is here; it
          does not answer yet. There is no corpus, no retrieval and no model call —
          those arrive in step&nbsp;3.
          <br />
          <br />
          This page exists to prove one thing: a change can travel from a branch,
          through CI, past a human approval, into <code>main</code>, and out to a live
          URL.
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
        Table feature slots. Each table mounts exactly one component here.

          <Citations />   Table 1
          <History />     Table 2
          <Guardrail />   Table 3
          <Feedback />    Table 4
          <AuditExport /> Table 5
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
