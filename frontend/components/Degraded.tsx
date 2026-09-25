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

export default function Degraded({ citations }: { citations: Citation[] }) {
  void citations;
  return null;
}
