/**
 * The kill switch, shown honestly. F4.
 *
 * REQ-U6: visibly degraded. There is no composed answer -- only the policy
 * sections that matched -- and the user is told so before they see them.
 */

import type { Citation } from "@/lib/types";

import Citations from "./Citations";

export default function Degraded({ citations }: { citations: Citation[] }) {
  return (
    <div>
      <div className="degraded" role="status">
        <strong>No answer could be composed.</strong> The assistant&rsquo;s
        answer service is off or unreachable. These are the policy sections
        that matched your question — read them directly; nothing below is an
        answer.
      </div>
      <Citations citations={citations} />
    </div>
  );
}
