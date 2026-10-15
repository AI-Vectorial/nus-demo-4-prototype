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

import Link from "next/link";

import type { Citation } from "@/lib/types";

/**
 * One citation per section (D7). Each links to that section in the corpus, by
 * heading (REQ-U15). A superseded citation is flagged (REQ-U4).
 */
export default function Citations({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;

  return (
    <ul className="citations" aria-label="Sources">
      {citations.map((c) => (
        <li key={`${c.document_id}|${c.version}|${c.section}`}>
          <Link
            href={`/corpus/${c.document_id}-${c.version}?section=${encodeURIComponent(c.section)}`}
            className={`citation ${c.status}`}
          >
            <span className="doc">{c.document_title}</span>
            <span className="section">{c.section}</span>
            <span className="version">version {c.version}</span>
            {c.status === "superseded" && <span className="badge">Superseded</span>}
          </Link>
        </li>
      ))}
    </ul>
  );
}
