"use client";

/**
 * The five policy documents. F7, REQ-B1 and REQ-B2.
 *
 * This is what lets someone check a citation rather than trust it, so the
 * things that decide whether a document still applies -- owner, version,
 * effective date, status -- are on the card, not behind it.
 */

import Link from "next/link";
import { useEffect, useState } from "react";

import Shell from "./Shell";
import StatusBadge from "./StatusBadge";
import { ArrowLeftIcon, ChevronRightIcon, PageIcon } from "./Icons";
import { ApiError, getCorpus } from "@/lib/api";
import { formatEffective } from "@/lib/format";
import type { CorpusListItem } from "@/lib/types";

/**
 * Two versions of the travel policy share one document id, so the id alone
 * does not name a document. Without the version, the superseded card opens
 * the current one -- which is exactly the confusion this corpus exists to
 * let a reader resolve.
 */
function corpusHref(doc: { id: string; version: string; status: string }): string {
  const base = `/corpus/${encodeURIComponent(doc.id)}`;
  return doc.status === "superseded"
    ? `${base}?version=${encodeURIComponent(doc.version)}`
    : base;
}

export default function CorpusList({ apiUrl }: { apiUrl: string }) {
  const [documents, setDocuments] = useState<CorpusListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    getCorpus(apiUrl)
      .then((result) => {
        if (live) setDocuments(result);
      })
      .catch((cause: unknown) => {
        if (!live) return;
        setError(
          cause instanceof ApiError ? cause.message : "Could not load the corpus.",
        );
      });
    return () => {
      live = false;
    };
  }, [apiUrl]);

  const count = documents?.length ?? 0;

  return (
    <Shell>
      <div className="page-scroll">
        <div className="page">
          {/* REQ-B6. The list needs a way back to the assistant that is not
              the chrome: an arrow alone is a guess, so it carries the word. */}
          <Link href="/" className="back-link">
            <ArrowLeftIcon />
            Back
          </Link>

          <div className="page-head">
            <h1 className="page-title">Corpus</h1>
            <p className="page-sub">
              {documents === null
                ? "Aldermere Bank internal policy"
                : `${count} ${count === 1 ? "document" : "documents"}`}
            </p>
          </div>

          {error && <p className="error-line">{error}</p>}
          {!error && documents === null && (
            <p className="pending">Loading the corpus…</p>
          )}

          {documents?.map((doc) => (
            <Link
              // A document id is shared across versions -- Travel and Expense
              // is in the corpus at both 3.1 and 3.0 -- so the key is not the id.
              key={`${doc.id}-${doc.version}`}
              href={corpusHref(doc)}
              className="doc-card"
            >
              <span className="thumb" aria-hidden="true">
                <PageIcon />
              </span>
              <span className="doc-body">
                <span className="doc-head">
                  <span className="doc-title">{doc.title}</span>
                  <StatusBadge status={doc.status} />
                </span>
                <span className="doc-meta">
                  {doc.owner} · v{doc.version} · effective{" "}
                  {formatEffective(doc.effective)}
                </span>
              </span>
              <span className="doc-chevron" aria-hidden="true">
                <ChevronRightIcon />
              </span>
            </Link>
          ))}
        </div>
      </div>
    </Shell>
  );
}
