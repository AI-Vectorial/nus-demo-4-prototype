"use client";

import { useEffect, useState } from "react";

type Health = {
  status: string;
  build: string;
  environment: string;
  dependencies: Record<string, string>;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [reachable, setReachable] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(`${API}/healthz`)
      .then((r) => r.json())
      .then((data: Health) => {
        setHealth(data);
        setReachable(true);
      })
      .catch(() => setReachable(false));
  }, []);

  return (
    <main className="wrap">
      <header>
        <h1>Policy Assistant</h1>
        <p className="lede">
          Ask a question about internal policy. Answers cite the sections they came
          from.
        </p>
      </header>

      {/* Step 1: the chat shell exists but does not yet answer. Retrieval and
          generation arrive in step 3, built through the pipeline itself. */}
      <section className="chat" aria-label="Conversation">
        <div className="placeholder">
          <strong>Step&nbsp;1 scaffold.</strong> The conversation surface is here; it
          does not answer yet. Retrieval, generation and the five table features land
          in later steps.
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
          placeholder="What is the policy on expense claims over SGD 500?"
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
        {reachable === null && <span className="mono dim">checking backend…</span>}
        {reachable === false && (
          <span className="mono bad">
            backend unreachable — is it running on {API}?
          </span>
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
