/**
 * The composed answer. F5.
 *
 * SHELL -- renders nothing until you implement it. The styles it needs already
 * exist in app/globals.css.
 *
 * REQ-U2: citations are visible WITHOUT further interaction. The brief assumes
 * that showing the source is what makes the answer trustworthy, so hiding them
 * behind a tab tests a different assumption.
 */

import type { AskResponse } from "@/lib/types";

export default function Answer({ response }: { response: AskResponse }) {
  if (response.outcome !== "answered" || response.answer === null) return null;

  return (
    <section className="answer" aria-label="Policy answer">
      <p>{response.answer}</p>
      <p className="mono dim">Answered in {response.latency_ms} ms</p>
    </section>
  );
}
