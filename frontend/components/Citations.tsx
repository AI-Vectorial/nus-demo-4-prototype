/**
 * The policy sections an answer came from. F5.
 *
 * REQ-U3: show document, section, version and status.
 * REQ-U4: a SUPERSEDED citation must be visibly distinguished. An answer that
 *         is correct but cites a withdrawn policy is the exact failure this
 *         product exists to prevent -- see the brief, section 3.
 * REQ-U15: a citation opens the section it names. A citation nobody can follow
 *         is a claim, not a source -- and checking the source is the whole
 *         reason the corpus browser exists.
 *
 * D7 -- one citation per document or one per passage -- is a decision for the
 * team, so this renders exactly what /ask returned and groups nothing. If the
 * team decides three passages from one document are one citation, that belongs
 * in the response, where the stored record (message_citations) agrees with what
 * the reader saw.
 */

import Link from "next/link";

import type { Citation } from "@/lib/types";

/**
 * Where a citation points.
 *
 * The section is passed by HEADING, not by anchor. The anchor a document page
 * builds includes the section's position in that document, which a citation has
 * no way of knowing -- and the corpus holds two versions of one policy whose
 * sections sit at different positions. The heading survives that; a position
 * does not.
 */
function citationHref(citation: Citation): string {
  const params = new URLSearchParams();
  if (citation.version) params.set("version", citation.version);
  if (citation.section) params.set("section", citation.section);
  const query = params.toString();
  return `/corpus/${encodeURIComponent(citation.document_id)}${query ? `?${query}` : ""}`;
}

export default function Citations({
  citations,
  label = "Sources",
}: {
  citations: Citation[];
  /** "Sources" under an answer; "Sections found" under a degraded response. */
  label?: string;
}) {
  if (citations.length === 0) return null;

  return (
    <div className="sources">
      <p className="sources-label">{label}</p>
      <ul className="citations">
        {citations.map((citation, index) => (
          <li
            // A document id is not unique across versions -- the corpus carries
            // Travel and Expense at both 3.0 and 3.1 -- so the section and
            // version join the key.
            key={`${citation.document_id}-${citation.version}-${citation.section}-${index}`}
            className={
              citation.status === "superseded" ? "citation superseded" : "citation"
            }
          >
            <Link href={citationHref(citation)} className="citation-link">
              <span className="doc">{citation.document_title}</span>
              <span className="section">{citation.section}</span>
              <span className="version">v{citation.version}</span>
              <span className="badge">{citation.status}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
