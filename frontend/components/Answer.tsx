/**
 * The composed answer. F5.
 *
 * REQ-U2: citations are visible WITHOUT further interaction -- the brief
 * assumes that showing the source is what makes the answer trustworthy.
 */

import Citations from "@/components/Citations";
import Markdown from "@/components/Markdown";
import type { AskResponse } from "@/lib/types";

export default function Answer({ response }: { response: AskResponse }) {
  return (
    <div className="answer">
      <Markdown>{response.answer ?? ""}</Markdown>
      <Citations citations={response.citations} />
    </div>
  );
}
