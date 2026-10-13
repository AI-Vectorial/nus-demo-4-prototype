/**
 * The composed answer, with its sources beneath it. F5.
 *
 * REQ-U2: citations are visible WITHOUT further interaction. Brief section 11:
 * the interface must make it unmissable that this is an answer about policy,
 * not a decision.
 */

import type { AskResponse } from "@/lib/types";

import Citations from "./Citations";
import Prose from "./Prose";

export default function Answer({ response }: { response: AskResponse }) {
  return (
    <div className="answer">
      <Prose text={response.answer ?? ""} />
      <p className="not-a-decision">
        This describes what policy says. It is not a decision — exceptions and
        judgement calls go to the policy&rsquo;s owning team.
      </p>
      <Citations citations={response.citations} />
    </div>
  );
}
