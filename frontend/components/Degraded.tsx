/**
 * The kill switch, shown honestly. F4.
 *
 * REQ-U6: degraded mode must be VISIBLY degraded. The model is off or
 * unreachable, so there is no composed answer -- only the policy sections that
 * were found.
 *
 * Showing those sections as though they were an answer is worse than an error,
 * because the user cannot tell. Say plainly that the assistant could not
 * compose an answer: less useful, still honest, still working.
 */

import Citations from "@/components/Citations";
import type { Citation } from "@/lib/types";

export default function Degraded({ citations }: { citations: Citation[] }) {
  return (
    <div>
      <p className="degraded">
        The assistant could not compose an answer right now. The policy sections
        it found are listed below. They are sources, not an answer.
      </p>
      <Citations citations={citations} />
    </div>
  );
}
