"use client";

/**
 * The assistant. F5.
 *
 * Empty state -> ask -> pending -> one of three outcomes, or an error. Each
 * renders differently (REQ-U5): an answer is a panel with its sources, a
 * refusal is dashed and neutral, degraded is flagged in red, and an error --
 * the product failing, not declining -- is its own solid red notice.
 *
 * Later questions join the same conversation, so every turn is recorded
 * together. Follow-up context (REQ-C3) is F6; Reset starts a new conversation.
 */

import { type FormEvent, useState } from "react";

import { ApiError, ask } from "@/lib/api";
import type { AskResponse } from "@/lib/types";

import Answer from "./Answer";
import Degraded from "./Degraded";
import Refusal from "./Refusal";
import TopBar from "./TopBar";

type Turn = {
  question: string;
  response?: AskResponse;
  error?: string;
};

function Outcome({ turn }: { turn: Turn }) {
  if (turn.error) {
    return (
      <div className="error" role="alert">
        <strong>Something went wrong — this is an error, not an answer.</strong>{" "}
        {turn.error} Try again in a moment.
      </div>
    );
  }
  const response = turn.response;
  if (!response) return <p className="pending">Searching the policy set…</p>;
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

  async function submit(event: FormEvent) {
    event.preventDefault();
    const question = draft.trim();
    if (!question || pending) return;

    setDraft("");
    setTurns((all) => [...all, { question }]);
    const settle = (patch: Partial<Turn>) =>
      setTurns((all) => all.map((t, i) => (i === all.length - 1 ? { ...t, ...patch } : t)));

    try {
      const response = await ask(apiUrl, question, conversationId);
      setConversationId(response.conversation_id);
      settle({ response });
    } catch (error) {
      settle({ error: error instanceof ApiError ? error.message : "Unexpected failure." });
    }
  }

  function reset() {
    setTurns([]);
    setConversationId(null);
    setDraft("");
  }

  const composer = (
    <form className="composer" onSubmit={submit}>
      <input
        aria-label="Your policy question"
        placeholder="Ask a policy question in your own words"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        disabled={pending}
        autoFocus
      />
      <button type="submit" disabled={pending || !draft.trim()}>
        Ask
      </button>
    </form>
  );

  return (
    <>
      <TopBar onReset={reset} />
      {turns.length === 0 ? (
        <main className="empty">
          <h1>What do you need to check?</h1>
          <p className="lede">
            Answers come only from Aldermere&rsquo;s policy set, with the sections
            they came from. If the policies do not cover it, you will be told who to ask.
          </p>
          {composer}
        </main>
      ) : (
        <main className="wrap">
          <div className="thread">
            {turns.map((turn, i) => (
              <section key={i} className="turn">
                <p className="question">{turn.question}</p>
                <Outcome turn={turn} />
              </section>
            ))}
          </div>
          {composer}
        </main>
      )}
    </>
  );
}
