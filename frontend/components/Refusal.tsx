/**
 * When the corpus cannot support an answer. F3.
 *
 * REQ-U5: different from an answer AND from an error -- a dashed outline, no
 * sources, and a heading that says the assistant declined. This is the
 * product working correctly.
 *
 * D5: the text comes from the API -- what the corpus covers, who owns each
 * policy, and Compliance for anything else.
 */

import Prose from "./Prose";

export default function Refusal({ reason }: { reason: string }) {
  return (
    <section className="refusal" aria-label="Not covered">
      <p className="lead">Not covered by the policy corpus</p>
      <Prose text={reason} />
    </section>
  );
}
