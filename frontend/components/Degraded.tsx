/**
 * The kill switch, shown honestly. F4.
 *
 * SHELL -- renders nothing until you implement it.
 *
 * REQ-U6: degraded mode must be VISIBLY degraded. The model is off or
 * unreachable, so there is no composed answer -- only the policy sections that
 * were found.
 *
 * Showing those sections as though they were an answer is worse than an error,
 * because the user cannot tell. Say plainly that the assistant could not
 * compose an answer: less useful, still honest, still working.
 */

import type { Citation } from "@/lib/types";
import Citations from "./Citations";

export default function Degraded({ citations }: { citations: Citation[] }) {
  return (
    <section className="degraded" role="status">
      <strong>No composed answer is available.</strong>
      <p>The assistant could not reach its answer-generation service. These are matching policy sources, not an answer.</p>
      {citations.length > 0 && <Citations citations={citations} />}
    </section>
  );
}
