/**
 * The composed answer. F5.
 *
 * REQ-U2: citations are visible WITHOUT further interaction -- the brief
 * assumes that showing the source is what makes the answer trustworthy.
 */

import Citations from "@/components/Citations";
import type { AskResponse } from "@/lib/types";

export default function Answer({ response }: { response: AskResponse }) {
  return (
    <div className="answer">
      <div className="answer-text">{response.answer}</div>
      <Citations citations={response.citations} />
    </div>
  );
}
