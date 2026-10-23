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
import Link from "next/link";

export default function Citations({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;

  return (
    <section className="citations" aria-label="Policy sources">
      <h3>Sources</h3>
      {citations.map((citation, index) => (
        <Link
          className={`citation ${citation.status === "superseded" ? "superseded" : ""}`}
          href={`/corpus/${encodeURIComponent(citation.document_id)}?version=${encodeURIComponent(citation.version)}&section=${encodeURIComponent(citation.section)}`}
          key={`${citation.document_id}:${citation.section}:${citation.version}:${index}`}
        >
          <span className="doc">{citation.document_title}</span>
          <span className="section">{citation.section}</span>
          <span className="version">v{citation.version}</span>
          {citation.status === "superseded" && (
            <span className="badge">Superseded</span>
          )}
        </Link>
      ))}
    </section>
  );
}
