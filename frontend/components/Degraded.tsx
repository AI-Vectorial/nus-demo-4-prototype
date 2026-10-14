/**
 * The kill switch, shown honestly. F4.
 *
 * REQ-U6: there is no composed answer -- only the policy sections that were
 * found, labelled as exactly that and never dressed up as an answer.
 */

import Citations from "@/components/Citations";
import type { Citation } from "@/lib/types";

export default function Degraded({ citations }: { citations: Citation[] }) {
  return (
    <div>
      <div className="degraded" role="status">
        <strong>No answer could be composed right now.</strong> The assistant&rsquo;s
        model is switched off or unreachable. These are the policy sections the
        search found. Read them directly; nothing below has been summarised.
      </div>
      <Citations citations={citations} showText />
    </div>
  );
}
