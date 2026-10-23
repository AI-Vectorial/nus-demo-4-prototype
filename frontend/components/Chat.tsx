"use client";

/**
 * The assistant. F5.
 *
 * REQ-U1 / REQ-U1b: an empty state that invites a question and offers three
 * questions the corpus can answer. One is the superseded-policy case, so the
 * first thing anyone sees is a citation flagged as withdrawn.
 * REQ-U2: the question, then the answer, with citations visible.
 * REQ-U5 / REQ-U6: refusal, degraded and error each render differently.
 * REQ-U7: a pending state while waiting.
 * REQ-U8: a follow-up keeps the conversation above it.
 * REQ-U9: Reset clears the conversation and starts a new one (REQ-C6).
 */

import { useRef, useState } from "react";

import Answer from "@/components/Answer";
import Degraded from "@/components/Degraded";
import Refusal from "@/components/Refusal";
import TopBar from "@/components/TopBar";
import { ApiError, ask } from "@/lib/api";
import type { AskResponse } from "@/lib/types";

const EXAMPLES = [
  "What is the approval threshold for a travel expense claim?",
  "Do I need approval for a claim of exactly £75?",
  "How long must client correspondence be kept?",
];

type Turn =
  | { kind: "question"; text: string }
  | { kind: "response"; response: AskResponse }
  | { kind: "error"; message: string };

export default function Chat({ apiUrl }: { apiUrl: string }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  // Bumped on Reset so a request still in flight cannot write into a new chat.
  const generation = useRef(0);

  async function send(text: string) {
    const question = text.trim();
    if (!question || pending) return;

    const current = generation.current;
    setDraft("");
    setPending(true);
    setTurns((t) => [...t, { kind: "question", text: question }]);

    try {
      const response = await ask(apiUrl, question, conversationId);
      if (current !== generation.current) return;
      setConversationId(response.conversation_id);
      setTurns((t) => [...t, { kind: "response", response }]);
    } catch (err) {
      if (current !== generation.current) return;
      const message =
        err instanceof ApiError ? err.message : "Something went wrong.";
      setTurns((t) => [...t, { kind: "error", message }]);
    } finally {
      if (current === generation.current) setPending(false);
    }
  }

  function reset() {
    generation.current += 1;
    setTurns([]);
    setConversationId(null);
    setDraft("");
    setPending(false);
  }

  return (
    <>
      <TopBar onReset={reset} />
      <main className="wrap">
        {turns.length === 0 ? (
          <section className="empty">
            <h1>Ask a policy question</h1>
            <p className="lede">
              Answers come only from Aldermere Bank&rsquo;s policy corpus, and
              every answer shows the sections it used.
            </p>
            <div className="examples">
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => send(example)}
                  disabled={pending}
                >
                  {example}
                </button>
              ))}
            </div>
          </section>
        ) : (
          <section className="chat" aria-live="polite">
            {turns.map((turn, i) => {
              if (turn.kind === "question") {
                return (
                  <p key={i} className="question">
                    {turn.text}
                  </p>
                );
              }
              if (turn.kind === "error") {
                return (
                  <div key={i} className="error" role="alert">
                    <span className="lead">Error.</span> {turn.message}
                  </div>
                );
              }
              const { response } = turn;
              if (response.outcome === "answered") {
                return <Answer key={i} response={response} />;
              }
              if (response.outcome === "refused") {
                return (
                  <Refusal
                    key={i}
                    reason={
                      response.answer ??
                      "Nothing in the corpus supports an answer to that question."
                    }
                  />
                );
              }
              return <Degraded key={i} citations={response.citations} />;
            })}
            {pending && <p className="pending">Searching the policy corpus…</p>}
          </section>
        )}

        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault();
            send(draft);
          }}
        >
          <input
            aria-label="Ask a policy question"
            placeholder="Ask about a policy…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            disabled={pending}
          />
          <button type="submit" disabled={pending || !draft.trim()}>
            Send
          </button>
        </form>
      </main>
    </>
  );
}
