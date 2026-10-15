"use client";

/**
 * F7 -- one document, its sections down the side, the text beside them.
 *
 * REQ-B3, REQ-B4: the section list moves the reader to the section.
 * REQ-U15: a citation arrives with ?section=<heading>. The section is found by
 * its HEADING, not by a position in the document, because two versions of the
 * same policy number their sections differently.
 * REQ-B6: a way back to the list, and to the assistant.
 */

import Link from "next/link";
import { useEffect, useState } from "react";

import { errorMessage, getDocument } from "@/lib/api";
import { Markdown } from "@/lib/markdown";
import type { DocumentDetail } from "@/lib/types";

function scrollToHeading(heading: string) {
  const target = Array.from(document.querySelectorAll<HTMLElement>("[data-heading]")).find(
    (el) => el.dataset.heading === heading,
  );
  target?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export default function CorpusDocument({
  apiUrl,
  documentId,
}: {
  apiUrl: string;
  documentId: string;
}) {
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDocument(apiUrl, documentId)
      .then((found) => {
        setDocument(found);
        const wanted = new URLSearchParams(window.location.search).get("section");
        if (wanted) {
          // Wait for the sections to render before looking for the heading.
          requestAnimationFrame(() => scrollToHeading(wanted));
        }
      })
      .catch((e: unknown) => setError(errorMessage(e)));
  }, [apiUrl, documentId]);

  if (error) {
    return (
      <main className="page">
        <p className="error-box">{error}</p>
        <p className="back-links">
          <Link href="/corpus">← All documents</Link>
        </p>
      </main>
    );
  }

  if (!document) {
    return (
      <main className="page">
        <p className="pending">Loading the document…</p>
      </main>
    );
  }

  return (
    <main className="page">
      <p className="back-links">
        <Link href="/corpus">← All documents</Link>
        <Link href="/">Ask the assistant</Link>
      </p>

      <h1>{document.title}</h1>
      <p className="dim">
        Version {document.version} · effective {document.effective} · {document.owner}
      </p>
      {document.status === "superseded" && (
        <p className="superseded-note">
          <span className="badge">Superseded</span> This version has been replaced.
          Answers that cite it are flagged.
        </p>
      )}

      <div className="doc-layout">
        <nav className="doc-sections" aria-label="Sections">
          <ol>
            {document.sections.map((section) => (
              <li key={section.heading}>
                <button type="button" onClick={() => scrollToHeading(section.heading)}>
                  {section.heading}
                </button>
              </li>
            ))}
          </ol>
        </nav>

        <div className="doc-body">
          {document.sections.map((section) => (
            <section
              key={section.heading}
              data-heading={section.heading}
              className="doc-section"
            >
              <h2>{section.heading}</h2>
              <Markdown source={section.text} />
            </section>
          ))}
        </div>
      </div>
    </main>
  );
}
