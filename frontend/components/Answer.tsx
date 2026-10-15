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

import { Markdown } from "@/lib/markdown";
import type { AskResponse } from "@/lib/types";

import Citations from "./Citations";

export default function Answer({ response }: { response: AskResponse }) {
  return (
    <div className="reply">
      <div className="answer" aria-label="Answer">
        <Markdown source={response.answer ?? ""} />
      </div>
      <Citations citations={response.citations} />
    </div>
  );
}
