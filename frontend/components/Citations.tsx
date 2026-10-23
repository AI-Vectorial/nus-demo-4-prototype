/**
 * The policy sections an answer came from. F5.
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
  if (citations.length === 0) return null;

  return (
    <ul className="citations" aria-label="Sources">
      {citations.map((c) => {
        const superseded = c.status === "superseded";
        return (
          <li
            key={`${c.document_id}-${c.section}`}
            className={superseded ? "citation superseded" : "citation"}
          >
            <span className="doc">{c.document_title}</span>
            <span className="section">{c.section}</span>
            <span className="version">v{c.version}</span>
            {superseded ? (
              <span className="badge">Superseded</span>
            ) : (
              <span className="dim">Current</span>
            )}
          </li>
        );
      })}
    </ul>
  );
}
