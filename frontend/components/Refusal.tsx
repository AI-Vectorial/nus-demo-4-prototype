/**
 * When the corpus cannot support an answer. F3.
 *
 * REQ-U5: different from an answer AND from an error -- this is the product
 * working correctly. D5: the API's message says what is not covered, lists
 * each policy's owning team, and points anything else at Compliance.
 */

import Prose from "./Prose";

export default function Refusal({ reason }: { reason: string }) {
  return (
    <div className="refusal" role="status">
      <p className="lead">Not covered by policy — no answer given</p>
      <div className="next">
        <Prose text={reason} />
      </div>
    </div>
  );
}
