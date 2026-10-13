/**
 * The policy sections an answer came from. F5.
 *
 * REQ-U2: always visible, no click needed. REQ-U3: document, section, version
 * and status. REQ-U4: a superseded citation is marked so it cannot be missed.
 * D7: one per document version and section -- the API has already grouped them.
 */

import type { Citation } from "@/lib/types";

export default function Citations({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return (
    <div className="citations" aria-label="Sources">
      <p className="citations-label">Sources</p>
      {citations.map((c) => (
        <div
          key={`${c.document_id}|${c.version}|${c.section}`}
          className={c.status === "superseded" ? "citation superseded" : "citation"}
        >
          <span className="doc">{c.document_title}</span>
          <span className="section">{c.section}</span>
          <span className="version">v{c.version}</span>
          {c.status === "superseded" && (
            <span className="badge">Superseded — do not rely on this version</span>
          )}
        </div>
      ))}
    </div>
  );
}
