"use client";

/**
 * The assistant. F5.
 *
 * Each exchange shows the question, a pending state, then exactly one of the
 * three outcomes -- or an error, which looks like none of them (REQ-U5).
 * A follow-up carries the conversation id, so the API answers it with the
 * recent turns in context (F6). A conversation reopened from History arrives
 * with its exchanges and continues the same way (F8). Reset starts a new
 * conversation; nothing saved is deleted.
 */

import { useRouter } from "next/navigation";
import { useState } from "react";

import Answer from "@/components/Answer";
import Degraded from "@/components/Degraded";
import Refusal from "@/components/Refusal";
import TopBar from "@/components/TopBar";
import { ApiError, ask } from "@/lib/api";
import type { AskResponse } from "@/lib/types";

export type Exchange = {
  question: string;
  response?: AskResponse;
  error?: string;
};

function Outcome({ exchange }: { exchange: Exchange }) {
  const { response, error } = exchange;
  if (error) return <p className="error">{error}</p>;
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

export default function Chat({
  apiUrl,
  conversationId: opened = null,
  initial = [],
  notice,
}: {
  apiUrl: string;
  conversationId?: string | null;
  initial?: Exchange[];
  notice?: string;
}) {
  const router = useRouter();
  const [exchanges, setExchanges] = useState<Exchange[]>(initial);
  const [conversationId, setConversationId] = useState<string | null>(opened);
  const [draft, setDraft] = useState("");
  const busy = exchanges.some((e) => !e.response && !e.error);

  async function send(event: React.FormEvent) {
    event.preventDefault();
    const question = draft.trim();
    if (!question || busy) return;
    setDraft("");
    const index = exchanges.length;
    setExchanges((all) => [...all, { question }]);
    const settle = (patch: Partial<Exchange>) =>
      setExchanges((all) => all.map((e, i) => (i === index ? { ...e, ...patch } : e)));
    try {
      const response = await ask(apiUrl, question, conversationId);
      setConversationId(response.conversation_id);
      settle({ response });
    } catch (error) {
      settle({
        error: error instanceof ApiError ? error.message : "Something went wrong.",
      });
    }
  }

  // C15: a new conversation with no prior context. Nothing saved is deleted.
  function reset() {
    setExchanges([]);
    setConversationId(null);
    setDraft("");
    router.replace("/");
  }

  const composer = (
    <form className="composer" onSubmit={send}>
      <input
        aria-label="Your question"
        placeholder="Ask about a policy…"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        disabled={busy}
      />
      <button type="submit" disabled={busy || !draft.trim()}>
        Send
      </button>
    </form>
  );

  return (
    <>
      <TopBar onReset={reset} />
      <main className="wrap">
        {notice && <p className="error">{notice}</p>}
        {exchanges.length === 0 ? (
          <section className="empty">
            <h1>Ask a policy question</h1>
            <p className="lede">
              Answers come only from Aldermere Bank&rsquo;s policies, with the
              sections they came from. If the policies do not cover it, the
              assistant says so.
            </p>
            {composer}
          </section>
        ) : (
          <>
            <section className="thread">
              {exchanges.map((exchange, i) => (
                <article key={i} className="exchange">
                  <p className="question">{exchange.question}</p>
                  <Outcome exchange={exchange} />
                </article>
              ))}
            </section>
            {composer}
          </>
        )}
      </main>
    </>
  );
}
