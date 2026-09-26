"use client";

/**
 * The assistant. F5, and F6's half of the conversation.
 *
 * Two states: an empty one that invites a question (REQ-U1), and a thread with
 * a composer pinned under it. The conversation id returned by the first answer
 * rides on every question after it (REQ-U8); Reset in the top bar drops it and
 * returns to the empty state (REQ-C6, REQ-U9).
 *
 * `?conversation=<id>` loads a stored thread and carries on from it (REQ-C9).
 * The id lives in the URL rather than in component state so that a row in
 * /history is an ordinary link -- and so the thread survives a refresh.
 */

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";

import Answer from "./Answer";
import Degraded from "./Degraded";
import Refusal from "./Refusal";
import Shell from "./Shell";
import { PersonIcon, SendIcon } from "./Icons";
import { ApiError, askWithConversation, getConversation } from "@/lib/api";
import type { AskResponse, ConversationMessage, Outcome } from "@/lib/types";

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

/**
 * useSearchParams suspends, and Next will not prerender a page that reads it
 * outside a boundary. The boundary belongs here, with the component that
 * created the requirement, rather than in every route that mounts one.
 */
export default function Chat({ apiUrl }: { apiUrl: string }) {
  return (
    <Suspense fallback={<Shell>{null}</Shell>}>
      <ChatThread apiUrl={apiUrl} />
    </Suspense>
  );
}

function ChatThread({ apiUrl }: { apiUrl: string }) {
  const router = useRouter();
  const requested = useSearchParams().get("conversation");

  const [turns, setTurns] = useState<Turn[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const [loaded, setLoaded] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const nextId = useRef(0);
  const threadEnd = useRef<HTMLDivElement>(null);

  // Derived rather than stored: a `loading` flag would have to be set as the
  // effect below starts, and a setState in an effect body is a cascading
  // render. What is being waited for is already in the URL.
  const loading = requested !== null && loaded !== requested && loadError === null;
  const started = turns.length > 0 || pending || loading || loadError !== null;

  useEffect(() => {
    threadEnd.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, pending]);

  // REQ-C9. Only when the URL asks for one: with no id this must leave the
  // conversation already in memory alone, which is what Reset depends on.
  useEffect(() => {
    if (!requested) return;

    let live = true;

    getConversation(apiUrl, requested)
      .then((conversation) => {
        if (!live) return;
        setConversationId(conversation.id);
        setTurns(
          conversation.messages.map((message) =>
            restore(message, nextId.current++, conversation.id),
          ),
        );
        setLoadError(null);
        setLoaded(requested);
      })
      .catch((cause: unknown) => {
        if (!live) return;
        setLoadError(
          cause instanceof ApiError
            ? cause.message
            : "Could not load that conversation.",
        );
      });

    return () => {
      live = false;
    };
  }, [apiUrl, requested]);

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
    setLoadError(null);
    // The id also lives in the URL. Leaving it there would reload the thread
    // that was just cleared the moment anything re-rendered. `loaded` is left
    // alone on purpose: it is only ever compared against the URL, and clearing
    // it before the URL catches up would show a load that is not happening.
    if (requested) router.replace("/");
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
              {loading && (
                <div className="msg assistant">
                  <p className="pending">Loading the conversation…</p>
                </div>
              )}
              {loadError && (
                <div className="msg assistant">
                  <p className="error-line">{loadError}</p>
                </div>
              )}
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

/**
 * A stored turn, rendered as the turn it was.
 *
 * A message from the record carries less than a fresh response does -- there
 * is no round trip to have taken -- so the fields that only describe the call
 * are filled in from what was stored, or zeroed.
 *
 * The outcome is the part that matters: it decides whether this reads as an
 * answer, a refusal or a degraded search. Every assistant turn records one, so
 * a missing outcome is not one of the three -- and it is passed through as
 * such, because guessing would render a stored refusal as an answer.
 */
function restore(
  message: ConversationMessage,
  id: number,
  conversationId: string,
): Turn {
  if (message.role === "user") {
    return { kind: "question", id, text: message.content ?? "" };
  }
  return {
    kind: "response",
    id,
    response: {
      outcome: (message.outcome ?? "unrecorded") as Outcome,
      answer: message.content,
      citations: message.citations ?? [],
      conversation_id: conversationId,
      message_id: message.id,
      latency_ms: message.latency_ms ?? 0,
    },
  };
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
