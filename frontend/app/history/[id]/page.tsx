"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import Citations from "@/components/Citations";
import Degraded from "@/components/Degraded";
import Refusal from "@/components/Refusal";
import TopBar from "@/components/TopBar";
import { ApiError, ask, getConversation } from "@/lib/api";
import type { ConversationDetail, ConversationMessage } from "@/lib/types";

export default function HistoryConversationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const [conversationId, setConversationId] = useState("");
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void params.then(({ id }) => {
      if (active) setConversationId(id);
    });
    return () => {
      active = false;
    };
  }, [params]);

  useEffect(() => {
    if (!conversationId) return;
    let active = true;
    void getConversation("/api", conversationId)
      .then((result) => {
        if (active) setConversation(result);
      })
      .catch((cause: unknown) => {
        if (active) {
          setError(cause instanceof ApiError ? cause.message : "Could not load this conversation.");
        }
      });
    return () => {
      active = false;
    };
  }, [conversationId]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || !conversationId || pending) return;

    setPending(true);
    setError(null);
    setQuestion("");
    try {
      const response = await ask("/api", trimmed, conversationId);
      const createdAt = new Date().toISOString();
      const userMessage: ConversationMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
        outcome: null,
        created_at: createdAt,
        citations: [],
      };
      const assistantMessage: ConversationMessage = {
        id: response.message_id,
        role: "assistant",
        content: response.answer,
        outcome: response.outcome,
        created_at: createdAt,
        citations: response.citations,
      };
      setConversation((current) =>
        current
          ? {
              ...current,
              last_at: createdAt,
              messages: [...current.messages, userMessage, assistantMessage],
            }
          : current,
      );
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "The follow-up request failed.");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="wrap">
      <TopBar showHistory />
      <div className="route-links">
        <Link href="/history">← All conversations</Link>
        <Link href="/">← Assistant</Link>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {!conversation && !error && <p role="status">Loading conversation…</p>}
      {conversation && (
        <>
          <header>
            <h1>Conversation</h1>
            <p className="lede">Started {new Date(conversation.started_at).toLocaleString()}</p>
          </header>
          <section className="history-thread" aria-live="polite">
            {conversation.messages.map((message) => (
              <article className="history-message" key={message.id}>
                {message.role === "user" ? (
                  <p className="user-question">{message.content}</p>
                ) : (
                  <>
                    {message.outcome === "answered" && (
                      <div className="answer"><p>{message.content}</p></div>
                    )}
                    {message.outcome === "refused" && (
                      <Refusal reason={message.content ?? ""} />
                    )}
                    {message.outcome === "degraded" && (
                      <Degraded citations={message.citations} />
                    )}
                    {message.outcome !== "degraded" && (
                      <Citations citations={message.citations} />
                    )}
                  </>
                )}
              </article>
            ))}
            {pending && <p className="pending" role="status">Searching the policy corpus…</p>}
          </section>
          <form className="composer" onSubmit={onSubmit}>
            <label className="sr-only" htmlFor="follow-up">Ask a follow-up</label>
            <input
              id="follow-up"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Continue this conversation…"
              disabled={pending}
            />
            <button type="submit" disabled={pending || !question.trim()}>
              Ask
            </button>
          </form>
        </>
      )}
    </main>
  );
}
