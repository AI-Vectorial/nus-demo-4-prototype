"use client";

import { FormEvent, useRef, useState } from "react";
import { ApiError, ask } from "@/lib/api";
import type { AskResponse } from "@/lib/types";
import TopBar from "./TopBar";
import Answer from "./Answer";
import Citations from "./Citations";
import Degraded from "./Degraded";
import Refusal from "./Refusal";

const EXAMPLE_QUESTIONS = [
  "What is the approval threshold for a travel expense claim?",
  "How often do we refresh KYC for a high-risk client?",
  "How long do we keep client correspondence?",
];

export default function Chat({ apiUrl }: { apiUrl: string }) {
  const [question, setQuestion] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [turns, setTurns] = useState<Array<{ question: string; response: AskResponse }>>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestGeneration = useRef(0);

  async function submitQuestion(value: string) {
    const trimmed = value.trim();
    if (!trimmed || pending) return;

    const generation = requestGeneration.current;
    setPending(true);
    setError(null);
    setQuestion("");
    try {
      const response = await ask(apiUrl, trimmed, conversationId);
      if (generation !== requestGeneration.current) return;
      setConversationId(response.conversation_id);
      setTurns((previous) => [...previous, { question: trimmed, response }]);
    } catch (cause) {
      if (generation !== requestGeneration.current) return;
      setError(cause instanceof ApiError ? cause.message : "The request failed.");
    } finally {
      if (generation === requestGeneration.current) setPending(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitQuestion(question);
  }

  function reset() {
    requestGeneration.current += 1;
    setTurns([]);
    setConversationId(null);
    setQuestion("");
    setError(null);
    setPending(false);
  }

  return (
    <main className="wrap">
      <TopBar onReset={reset} showHistory />
      <header>
        <h1>Ask about policy</h1>
        <p className="lede">Answers use Aldermere policy sources. This assistant explains policy; it does not make decisions.</p>
      </header>
      <section className="chat" aria-live="polite">
        {turns.length === 0 ? (
          <div className="placeholder">
            <strong>What would you like to know?</strong>
            <p>Choose an example or ask in your own words.</p>
            <div className="examples">
              {EXAMPLE_QUESTIONS.map((example) => (
                <button
                  className="example"
                  key={example}
                  type="button"
                  disabled={pending}
                  onClick={() => void submitQuestion(example)}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <ol className="turns">
            {turns.map(({ question: asked, response }, index) => (
              <li className="turn" key={`${response.message_id}-${index}`}>
                <p className="user-question">{asked}</p>
                {response.outcome === "answered" && <Answer response={response} />}
                {response.outcome === "refused" && <Refusal reason={response.answer ?? ""} />}
                {response.outcome === "degraded" && <Degraded citations={response.citations} />}
                {response.outcome !== "degraded" && (
                  <Citations citations={response.citations} />
                )}
              </li>
            ))}
          </ol>
        )}
        {pending && <p className="pending" role="status">Searching the policy corpus…</p>}
        {error && <p className="error" role="alert">{error}</p>}
      </section>
      <form className="composer" onSubmit={onSubmit}>
        <label className="sr-only" htmlFor="question">Your policy question</label>
        <input
          id="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a policy question…"
          disabled={pending}
        />
        <button type="submit" disabled={pending || !question.trim()}>Ask</button>
      </form>
      <footer><p className="dim">Aldermere Bank is fictional. Check the cited policy source before acting.</p></footer>
    </main>
  );
}
