/**
 * The policy sections an answer came from. F5.
 *
 * REQ-U3: document, section, version and status on every citation.
 * REQ-U4: a superseded citation carries a "Superseded" label in the warning
 *         colours -- criterion 28, in the team's words.
 * D7: one citation per passage, de-duplicated by the API.
 */

import type { Citation } from "@/lib/types";

export default function Citations({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return (
    <ul className="citations" aria-label="Sources">
      {citations.map((c) => (
        <li
          key={`${c.document_id}|${c.version}|${c.section}`}
          className={`citation ${c.status}`}
        >
          <span className="doc">{c.document_title}</span>
          <span className="section">{c.section}</span>
          <span className="version">v{c.version}</span>
          {c.status === "superseded" ? (
            <span className="badge">Superseded</span>
          ) : (
            <span className="status">current</span>
          )}
        </li>
      ))}
    </ul>
  );
}
