"use client";

/**
 * The assistant. F5.
 *
 * Empty state (REQ-U1) -> question shown at once with a pending state (REQ-U2,
 * REQ-U7) -> one of three outcomes, or an error (REQ-U5, REQ-U6). Later
 * questions go to the same conversation, and everything above stays (REQ-C1,
 * criterion 35). Follow-up context is F6 -- not in this increment.
 */

import { type FormEvent, useEffect, useRef, useState } from "react";

import { ApiError, ask } from "@/lib/api";
import type { AskResponse } from "@/lib/types";
import Answer from "./Answer";
import Degraded from "./Degraded";
import ErrorNotice from "./ErrorNotice";
import Refusal from "./Refusal";
import { RESET_EVENT } from "./TopBar";

type Turn = {
  id: number;
  question: string;
  response?: AskResponse;
  error?: string;
};

function Outcome({ turn }: { turn: Turn }) {
  if (turn.error) return <ErrorNotice message={turn.error} />;
  const response = turn.response;
  if (!response) return <p className="pending">Searching the policies…</p>;
  switch (response.outcome) {
    case "answered":
      return <Answer response={response} />;
    case "refused":
      return <Refusal reason={response.answer ?? ""} />;
    case "degraded":
      return <Degraded citations={response.citations} />;
  }
}

export default function Chat({ apiUrl }: { apiUrl: string }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const pending = turns.some((t) => !t.response && !t.error);
  // Bumped by Reset, so a response still in flight cannot re-attach the
  // conversation that was just dropped.
  const generation = useRef(0);

  useEffect(() => {
    const reset = () => {
      generation.current += 1;
      setTurns([]);
      setConversationId(null);
      setDraft("");
    };
    window.addEventListener(RESET_EVENT, reset);
    return () => window.removeEventListener(RESET_EVENT, reset);
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const question = draft.trim();
    if (!question || pending) return;

    const id = Date.now();
    const started = generation.current;
    setTurns((all) => [...all, { id, question }]);
    setDraft("");

    const settle = (patch: Partial<Turn>) => {
      if (generation.current !== started) return;
      setTurns((all) => all.map((t) => (t.id === id ? { ...t, ...patch } : t)));
    };
    try {
      const response = await ask(apiUrl, question, conversationId);
      if (generation.current !== started) return;
      setConversationId(response.conversation_id);
      settle({ response });
    } catch (error) {
      settle({
        error: error instanceof ApiError ? error.message : "Something unexpected went wrong.",
      });
    }
  }

  const composer = (
    <form className="composer" onSubmit={submit}>
      <input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        placeholder="Ask a policy question…"
        aria-label="Your question"
        disabled={pending}
        autoFocus
      />
      <button type="submit" disabled={pending || !draft.trim()}>
        Send
      </button>
    </form>
  );

  if (!turns.length) {
    return (
      <main className="empty">
        <h1>What does the policy say?</h1>
        <p className="lede">
          Ask about Aldermere policy in your own words. Answers come only from the policy
          documents, and show the sections they used.
        </p>
        {composer}
      </main>
    );
  }

  return (
    <main className="wrap conversation">
      {turns.map((turn) => (
        <article key={turn.id} className="turn">
          <p className="question">{turn.question}</p>
          <Outcome turn={turn} />
        </article>
      ))}
      {composer}
    </main>
  );
}
