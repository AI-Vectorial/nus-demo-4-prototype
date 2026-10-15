"use client";

/** F7 -- the five documents (REQ-B1, REQ-B2). */

import Link from "next/link";
import { useEffect, useState } from "react";

import { errorMessage, listCorpus } from "@/lib/api";
import type { DocumentSummary } from "@/lib/types";

export default function CorpusList({ apiUrl }: { apiUrl: string }) {
  const [documents, setDocuments] = useState<DocumentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCorpus(apiUrl)
      .then(setDocuments)
      .catch((e: unknown) => setError(errorMessage(e)));
  }, [apiUrl]);

  return (
    <main className="page">
      <h1>Policy corpus</h1>
      <p className="dim">
        The documents the assistant answers from. Every one is read from the
        corpus folder; nothing is copied.
      </p>

      {error && <p className="error-box">{error}</p>}
      {!documents && !error && <p className="pending">Loading the documents…</p>}

      <ul className="doc-list">
        {documents?.map((document) => (
          <li key={document.id}>
            <Link
              href={`/corpus/${document.id}`}
              className={`doc-card ${document.status}`}
            >
              <span className="doc-title">{document.title}</span>
              <span className="doc-meta">
                Version {document.version} · effective {document.effective} · {document.owner}
              </span>
              {document.status === "superseded" && (
                <span className="badge">Superseded</span>
              )}
            </Link>
          </li>
        ))}
      </ul>

      <p className="back-links">
        <Link href="/">← Ask the assistant</Link>
      </p>
    </main>
  );
}
