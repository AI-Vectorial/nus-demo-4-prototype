/**
 * The kill switch, shown honestly. F4.
 *
 * REQ-U6: the model is off or unreachable, so there is NO composed answer.
 * The heading says so first, and the sections below are labelled as what
 * search found -- never presented as though they were an answer.
 */

import type { Citation } from "@/lib/types";
import Citations from "./Citations";

export default function Degraded({ citations }: { citations: Citation[] }) {
  return (
    <section className="degraded-result" aria-label="No answer composed">
      <div className="degraded">
        <strong>No answer could be composed right now.</strong> The assistant&rsquo;s
        writing step is unavailable. These are the policy sections search found for
        your question — read them directly.
      </div>
      <p className="found">Sections found</p>
      <Citations citations={citations} />
    </section>
  );
}
