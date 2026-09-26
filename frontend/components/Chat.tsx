"use client";

/**
 * The page a table lands on before they have built anything.
 *
 * It says what is running, what is not, and where to start -- and it says the
 * true thing. An earlier version claimed "the corpus is indexed and waiting",
 * which was false: indexing it is F1, the first thing a table builds. A
 * scaffold that misreports its own state teaches the wrong lesson on the first
 * screen anyone sees.
 *
 * Replacing this with the real assistant is F5. Nothing here is precious.
 */

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
    <main className="welcome">
      <header className="welcome-head">
        <p className="eyebrow">M04 · AI-Native Development Lifecycle</p>
        <h1>Policy Assistant</h1>
        <p className="lede">
          You are going to build this, and deploy it. A staff member at
          Aldermere Bank asks a policy question in plain language; the assistant
          answers <strong>only</strong> from the bank&rsquo;s policy corpus and
          shows which sections it used. When the corpus cannot support an
          answer, <strong>it says so and stops.</strong>
        </p>
      </header>

      <section className="card">
        <h2>What is running</h2>
        <ul className="status-list">
          <li>
            <span className="status-name">API</span>
            <span className={reachable === false ? "status-bad" : "status-ok"}>
              {reachable === null
                ? "checking…"
                : reachable
                  ? "reachable on :8000"
                  : `unreachable at ${apiUrl}`}
            </span>
          </li>
          {health &&
            Object.entries(health.dependencies).map(([name, detail]) => (
              <li key={name}>
                <span className="status-name">{name.replace(/_/g, " ")}</span>
                <span
                  className={
                    detail.startsWith("down") ? "status-bad" : "status-ok"
                  }
                >
                  {detail}
                </span>
              </li>
            ))}
        </ul>
        <p className="note">
          Postgres and Qdrant are running beside you in this Codespace, and they
          are yours alone. <strong>The corpus is not indexed yet</strong> —
          indexing it is the first thing you build.
        </p>
      </section>

      <section className="card">
        <h2>Where to start</h2>
        <ol className="start-list">
          <li>
            <code>START-HERE.md</code> — ninety seconds, already open in your
            editor
          </li>
          <li>
            <code>docs/PRD.md</code> — what must be true. The contract.{" "}
            <strong>§10 is the one to read twice</strong>
          </li>
          <li>
            <code>pipeline/01-shape.md</code> — then follow the six stages in
            order
          </li>
        </ol>
        <p className="note">
          Ten decisions in §10 are deliberately left to you.{" "}
          <strong>You will be asked to defend them</strong>, and{" "}
          <em>&ldquo;the agent chose it&rdquo;</em> is a failed answer.
        </p>
      </section>

      <p className="footnote">
        Aldermere Bank is fictional. This screen is scaffolding — replacing it
        is F5.
      </p>
    </main>
  );
}
