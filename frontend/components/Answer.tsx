/**
 * The composed answer. F5.
 *
 * REQ-U2: citations are visible WITHOUT further interaction. The brief assumes
 * that showing the source is what makes the answer trustworthy, so hiding them
 * behind a tab tests a different assumption.
 */

import Citations from "./Citations";
import { paragraphs } from "@/lib/format";
import type { AskResponse } from "@/lib/types";

export default function Answer({ response }: { response: AskResponse }) {
  // An "answered" outcome without text would be a backend bug, not a refusal --
  // saying so is better than rendering an empty card that reads as an answer.
  const body = paragraphs(response.answer ?? "");

  return (
    <div className="answer">
      {body.length > 0 ? (
        body.map((para, index) => <p key={index}>{para}</p>)
      ) : (
        <p className="dim">The API returned an answer with no text.</p>
      )}
      <Citations citations={response.citations} />
    </div>
  );
}
