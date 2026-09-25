"use client";

/**
 * The assistant. F5, and F6's half of the conversation.
 *
 * Two states: an empty one that invites a question (REQ-U1), and a thread with
 * a composer pinned under it. The conversation id returned by the first answer
 * rides on every question after it (REQ-U8); Reset in the top bar drops it and
 * returns to the empty state (REQ-C6, REQ-U9).
 */

import { useEffect, useRef, useState } from "react";

import Answer from "./Answer";
import Degraded from "./Degraded";
import Refusal from "./Refusal";
import Shell from "./Shell";
import { PersonIcon, SendIcon } from "./Icons";
import { ApiError, askWithConversation } from "@/lib/api";
import type { AskResponse } from "@/lib/types";

/** The three the demo is built around: an answer, a refresh cycle, a conflict. */
const SUGGESTIONS = [
  "What is the approval threshold for a travel expense claim?",
  "How often do we refresh KYC for a high-risk client?",
  "How long do we keep client correspondence?",
];

type Turn =
  | { kind: "question"; id: number; text: string }
  | { kind: "response"; id: number; response: AskResponse }
  | { kind: "error"; id: number; message: string };

export default function Chat({ apiUrl }: { apiUrl: string }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);

  const nextId = useRef(0);
  const threadEnd = useRef<HTMLDivElement>(null);

  const started = turns.length > 0 || pending;

  useEffect(() => {
    threadEnd.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, pending]);

  async function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || pending) return;

    setQuestion("");
    setTurns((current) => [
      ...current,
      { kind: "question", id: nextId.current++, text: trimmed },
    ]);
    setPending(true);

    try {
      const response = await askWithConversation(apiUrl, trimmed, conversationId);
      setConversationId(response.conversation_id);
      setTurns((current) => [
        ...current,
        { kind: "response", id: nextId.current++, response },
      ]);
    } catch (error) {
      // A transport failure, not a refusal. REQ-U5 needs the two to read
      // differently, so this renders as neither an answer nor a refusal card.
      const message =
        error instanceof ApiError
          ? error.message
          : "Something went wrong while asking.";
      setTurns((current) => [
        ...current,
        { kind: "error", id: nextId.current++, message },
      ]);
    } finally {
      setPending(false);
    }
  }

  /**
   * Reset. The conversation id goes with the turns -- keeping it would
   * silently answer the next question with the thread the reader just
   * cleared, which is the opposite of what the word promises.
   */
  function reset() {
    setTurns([]);
    setConversationId(null);
    setQuestion("");
  }

  function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    void submit(question);
  }

  return (
    <Shell onReset={reset}>
      {started ? (
        <>
          <div className="thread-scroll">
            <div className="thread" aria-live="polite">
              {turns.map((turn) => (
                <TurnView key={turn.id} turn={turn} />
              ))}
              {pending && (
                // REQ-U7. Four seconds of nothing reads as broken.
                <div className="msg assistant">
                  <p className="pending">Searching the policy corpus…</p>
                </div>
              )}
              <div ref={threadEnd} />
            </div>
          </div>

          <div className="composer-bar">
            <form className="ask-form" onSubmit={onSubmit}>
              <label className="sr-only" htmlFor="question">
                Ask a follow-up
              </label>
              <input
                id="question"
                className="field"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask a follow-up"
                autoComplete="off"
              />
              <SendButton disabled={!question.trim() || pending} />
            </form>
          </div>
        </>
      ) : (
        <div className="empty">
          <h1 className="empty-title">What does the policy say?</h1>
          <p className="lede">
            Aldermere&rsquo;s policy corpus, answered in plain language. Every answer
            shows the sections it came from.
          </p>

          <form className="ask-form" onSubmit={onSubmit}>
            <label className="sr-only" htmlFor="question">
              Your question
            </label>
            <input
              id="question"
              className="field"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask about travel, KYC, retention or outsourcing"
              autoComplete="off"
              autoFocus
            />
            <SendButton disabled={!question.trim() || pending} />
          </form>

          <ul className="chips">
            {SUGGESTIONS.map((suggestion) => (
              <li key={suggestion}>
                <button
                  type="button"
                  className="chip"
                  onClick={() => void submit(suggestion)}
                >
                  {suggestion}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Shell>
  );
}

function SendButton({ disabled }: { disabled: boolean }) {
  return (
    <button type="submit" className="send" disabled={disabled} aria-label="Ask">
      <SendIcon />
    </button>
  );
}

function TurnView({ turn }: { turn: Turn }) {
  if (turn.kind === "question") {
    return (
      <div className="msg user">
        <p className="bubble-user">{turn.text}</p>
        <span className="avatar" aria-hidden="true">
          <PersonIcon />
        </span>
      </div>
    );
  }

  if (turn.kind === "error") {
    return (
      <div className="msg assistant">
        <p className="error-line">{turn.message} Try asking again.</p>
      </div>
    );
  }

  return (
    <div className="msg assistant">
      <div className="msg-assistant">
        <Outcome response={turn.response} />
      </div>
    </div>
  );
}

function Outcome({ response }: { response: AskResponse }) {
  switch (response.outcome) {
    case "answered":
      return <Answer response={response} />;
    case "refused":
      return <Refusal reason={response.answer ?? ""} />;
    case "degraded":
      return <Degraded citations={response.citations} />;
    default:
      // The outcome is explicit by contract (PRD section 5). If an unknown one
      // arrives, say so rather than guessing which of the three it meant.
      return (
        <p className="error-line">
          The API returned an outcome this interface does not recognise.
        </p>
      );
  }
}
