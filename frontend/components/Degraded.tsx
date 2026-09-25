/**
 * The kill switch, shown honestly. F4.
 *
 * REQ-U6: degraded mode must be VISIBLY degraded. The model is off or
 * unreachable, so there is no composed answer -- only the policy sections that
 * were found.
 *
 * Showing those sections as though they were an answer is worse than an error,
 * because the user cannot tell. So the banner says plainly what is missing
 * before the sections appear, and the sections are labelled "Sections found"
 * rather than "Sources": nothing here sourced anything.
 */

import Citations from "./Citations";
import type { Citation } from "@/lib/types";

export default function Degraded({ citations }: { citations: Citation[] }) {
  return (
    <>
      <p className="degraded">
        The assistant could not compose an answer — the model is switched off or
        unreachable. These are the policy sections your question matched. Read them
        yourself; nothing below has been summarised.
      </p>
      <div className="answer">
        {citations.length > 0 ? (
          <Citations citations={citations} label="Sections found" />
        ) : (
          <p className="dim">No policy sections matched this question either.</p>
        )}
      </div>
    </>
  );
}
