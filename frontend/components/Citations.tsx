/**
 * The policy sections an answer came from. F5.
 *
 * SHELL -- renders nothing until you implement it.
 *
 * REQ-U3: show document, section, version and status.
 * REQ-U4: a SUPERSEDED citation must be visibly distinguished. An answer that
 *         is correct but cites a withdrawn policy is the exact failure this
 *         product exists to prevent -- see the brief, section 3.
 *
 * D7 is yours: three passages from one document -- one citation, or three?
 */

import type { Citation } from "@/lib/types";

export default function Citations({ citations }: { citations: Citation[] }) {
  void citations;
  return null;
}
