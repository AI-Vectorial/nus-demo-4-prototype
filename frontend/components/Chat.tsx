"use client";

/**
 * The assistant. F5 (ask, and the three outcomes), F6 (follow-ups) and F8
 * (a past conversation opened from History and continued).
 */

import { useEffect, useRef, useState } from "react";

import { ask, errorMessage, getConversation } from "@/lib/api";
import { RESET_EVENT } from "@/lib/reset";
import type { AskResponse, ConversationView, Outcome } from "@/lib/types";

import Answer from "./Answer";
import Degraded from "./Degraded";
import Refusal from "./Refusal";

// REQ-U1b: three questions the corpus can answer or decline. One is about the
// superseded travel policy, so the first thing anyone sees is a flagged citation.
const EXAMPLES = [
  "What is the approval threshold for a travel expense claim?",
  "How long can a provider keep our client correspondence after we terminate?",
  "Can I expense my partner's flight if they travel with me?",
];

type Turn =
  | { kind: "question"; text: string }
  | { kind: "reply"; response: AskResponse }
  | { kind: "error"; text: string };

function fromStored(view: ConversationView): Turn[] {
  return view.messages.map((m): Turn =>
    m.role === "user"
      ? { kind: "question", text: m.content ?? "" }
      : {
          kind: "reply",
          response: {
            outcome: (m.outcome ?? "answered") as Outcome,
            answer: m.content,
            citations: m.citations,
            conversation_id: view.id,
            message_id: m.id,
            latency_ms: 0,
          },
        },
  );
}

function Reply({ response }: { response: AskResponse }) {
  if (response.outcome === "refused") return <Refusal reason={response.answer ?? ""} />;
  if (response.outcome === "degraded") return <Degraded citations={response.citations} />;
  return <Answer response={response} />;
}

export default function Chat({
  apiUrl,
  initialConversationId = null,
}: {
  apiUrl: string;
  initialConversationId?: string | null;
}) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(initialConversationId);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  // Opening a past conversation from History (REQ-C9).
  useEffect(() => {
    if (!initialConversationId) return;
    let cancelled = false;
    getConversation(apiUrl, initialConversationId)
      .then((view) => {
        if (!cancelled) setTurns(fromStored(view));
      })
      .catch((e: unknown) => {
        if (!cancelled) setLoadError(errorMessage(e));
      });
    return () => {
      cancelled = true;
    };
  }, [apiUrl, initialConversationId]);

  // Reset starts a fresh conversation with no prior context (REQ-C6).
  useEffect(() => {
    function reset() {
      setTurns([]);
      setConversationId(null);
      setDraft("");
      setLoadError(null);
    }
    window.addEventListener(RESET_EVENT, reset);
    return () => window.removeEventListener(RESET_EVENT, reset);
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [turns.length, pending]);

  async function submit(text: string) {
    const question = text.trim();
    if (!question || pending) return;
    setDraft("");
    setPending(true);
    setTurns((t) => [...t, { kind: "question", text: question }]);
    try {
      const response = await ask(apiUrl, question, conversationId);
      setConversationId(response.conversation_id);
      setTurns((t) => [...t, { kind: "reply", response }]);
    } catch (e) {
      setTurns((t) => [...t, { kind: "error", text: errorMessage(e) }]);
    } finally {
      setPending(false);
    }
  }

  const empty = turns.length === 0 && !pending && !loadError;

  return (
    <main className="assistant">
      <div className="transcript">
        {empty && (
          <section className="empty">
            <h1>Ask a policy question</h1>
            <p className="dim">
              Answers come only from the Aldermere policy documents, with the sections
              they came from. If the documents do not cover a question, the assistant
              says so.
            </p>
            <div className="examples">
              {EXAMPLES.map((q) => (
                <button key={q} type="button" onClick={() => submit(q)} disabled={pending}>
                  {q}
                </button>
              ))}
            </div>
          </section>
        )}

        {loadError && (
          <p className="error-box" role="alert">
            {loadError}
          </p>
        )}

        {turns.map((turn, index) => {
          if (turn.kind === "question") {
            return (
              <p key={index} className="question">
                {turn.text}
              </p>
            );
          }
          if (turn.kind === "error") {
            return (
              <p key={index} className="error-box" role="alert">
                {turn.text}
              </p>
            );
          }
          return <Reply key={index} response={turn.response} />;
        })}

        {pending && <p className="pending">Searching the policy and composing an answer…</p>}
        <div ref={endRef} />
      </div>

      <form
        className="composer"
        onSubmit={(event) => {
          event.preventDefault();
          submit(draft);
        }}
      >
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask about policy…"
          aria-label="Your question"
          maxLength={2000}
          disabled={pending}
        />
        <button type="submit" disabled={pending || !draft.trim()}>
          Ask
        </button>
      </form>
    </main>
  );
}

