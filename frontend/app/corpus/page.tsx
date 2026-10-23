"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { ApiError, listCorpus } from "@/lib/api";
import type { CorpusDocument } from "@/lib/types";

export default function CorpusPage() {
  const [documents, setDocuments] = useState<CorpusDocument[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    void listCorpus("/api")
      .then((result) => {
        if (active) setDocuments(result);
      })
      .catch((cause: unknown) => {
        if (active) {
          setError(cause instanceof ApiError ? cause.message : "Could not load the policy corpus.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="wrap">
      <TopBar showHistory />
      <header>
        <h1>Policy corpus</h1>
        <p className="lede">Browse the policy sources used by the assistant.</p>
      </header>
      <section className="corpus-list" aria-label="Policy documents">
        {loading && <p role="status">Loading policy documents…</p>}
        {error && <p className="error" role="alert">{error}</p>}
        {documents.map((document) => (
          <Link
            className={`corpus-document ${document.status === "superseded" ? "superseded" : ""}`}
            href={`/corpus/${encodeURIComponent(document.id)}?version=${encodeURIComponent(document.version)}`}
            key={`${document.id}:${document.version}`}
          >
            <span className="corpus-document-title">{document.title}</span>
            <span>Owner: {document.owner}</span>
            <span>Version {document.version} · Effective {document.effective}</span>
            <span className="corpus-status">{document.status}</span>
          </Link>
        ))}
      </section>
      <footer><p className="dim">Policy documents are read-only sources.</p></footer>
    </main>
  );
}
