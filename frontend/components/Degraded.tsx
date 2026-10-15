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

/** REQ-U6: visibly degraded. The passages are shown as sources, never as an answer. */
export default function Degraded({ citations }: { citations: Citation[] }) {
  return (
    <div className="reply">
      <div className="degraded" role="alert">
        <strong>No answer was composed.</strong> The assistant could not compose an
        answer right now. These are the policy sections it found; read them directly.
      </div>
      <Citations citations={citations} />
    </div>
  );
}
