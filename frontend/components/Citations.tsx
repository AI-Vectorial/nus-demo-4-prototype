/**
 * The policy sections an answer came from. F5.
 *
 * REQ-U3: document, section, version and status.
 * REQ-U4: a SUPERSEDED citation is impossible to miss.
 *
 * D7 (table 3): the API keeps one citation per section; here they are grouped
 * under their document and version, so a reader sees "Travel and Expense
 * Policy v3.1 -- current" once with its sections beneath. Grouping is
 * presentation only: every section keeps its own row.
 */

import type { Citation } from "@/lib/types";

type Group = { key: string; first: Citation; sections: Citation[] };

function grouped(citations: Citation[]): Group[] {
  const groups = new Map<string, Group>();
  for (const c of citations) {
    const key = `${c.document_id}@${c.version}`;
    const group = groups.get(key) ?? { key, first: c, sections: [] };
    group.sections.push(c);
    groups.set(key, group);
  }
  return [...groups.values()];
}

export default function Citations({
  citations,
  showText = false,
}: {
  citations: Citation[];
  showText?: boolean;
}) {
  if (citations.length === 0) return null;
  return (
    <div className="citations" aria-label="Sources">
      {grouped(citations).map(({ key, first, sections }) => {
        const superseded = first.status === "superseded";
        return (
          <div key={key} className={`citation${superseded ? " superseded" : ""}`}>
            <span className="doc">{first.document_title}</span>
            <span className="version">v{first.version}</span>
            {superseded ? (
              <span className="badge">Superseded</span>
            ) : (
              <span className="dim">current</span>
            )}
            <ul className="sections">
              {sections.map((c) => (
                <li key={c.section}>
                  <span className="section">{c.section}</span>
                  {showText && c.text && <p className="passage">{c.text}</p>}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
