/**
 * The composed answer. F5.
 *
 * REQ-U2: citations are visible WITHOUT further interaction. The brief assumes
 * that showing the source is what makes the answer trustworthy, so hiding them
 * behind a tab tests a different assumption.
 *
 * The model writes Markdown whether or not it is asked to -- a threshold comes
 * back as **£75** more often than not -- so the paragraphs go through the
 * inline pass of the corpus renderer. Literal asterisks around a number read
 * as a broken product, and the number is the part the reader came for.
 */

import Citations from "./Citations";
import { paragraphs } from "@/lib/format";
import { InlineMarkdown } from "@/lib/markdown";
import type { AskResponse } from "@/lib/types";

export default function Answer({ response }: { response: AskResponse }) {
  // An "answered" outcome without text would be a backend bug, not a refusal --
  // saying so is better than rendering an empty card that reads as an answer.
  const body = paragraphs(response.answer ?? "");

  return (
    <div className="answer">
      {body.length > 0 ? (
        body.map((para, index) => (
          <p key={index}>
            <InlineMarkdown text={para} />
          </p>
        ))
      ) : (
        <p className="dim">The API returned an answer with no text.</p>
      )}
      <Citations citations={response.citations} />
    </div>
  );
}
