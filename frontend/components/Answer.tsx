/**
 * The composed answer. F5.
 *
 * REQ-U2: citations are visible WITHOUT further interaction. The brief assumes
 * that showing the source is what makes the answer trustworthy, so hiding them
 * behind a tab tests a different assumption.
 */

import type { AskResponse } from "@/lib/types";
import Citations from "@/components/Citations";

export default function Answer({ response }: { response: AskResponse }) {
  return (
    <div className="answer">
      <p className="answer-text">{response.answer}</p>
      <Citations citations={response.citations} />
    </div>
  );
}
