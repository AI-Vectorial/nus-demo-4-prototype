/**
 * The composed answer. F5.
 *
 * REQ-U2: citations are visible WITHOUT further interaction -- they render
 * directly beneath the answer, not behind a tab.
 */

import type { AskResponse } from "@/lib/types";
import Citations from "./Citations";
import Prose from "./Prose";

export default function Answer({ response }: { response: AskResponse }) {
  return (
    <section className="answer" aria-label="Answer">
      <Prose text={response.answer ?? ""} />
      <Citations citations={response.citations} />
      <p className="notice">
        What the policy says — not a decision. Exceptions and judgement calls go to a person.
      </p>
    </section>
  );
}
