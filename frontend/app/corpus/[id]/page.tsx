"use client";

import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { ApiError, getCorpusDocument } from "@/lib/api";
import type { CorpusDocumentDetail } from "@/lib/types";

export default function CorpusDocumentPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ version?: string; section?: string }>;
}) {
  const [documentId, setDocumentId] = useState("");
  const [version, setVersion] = useState<string | undefined>();
  const [section, setSection] = useState<string | undefined>();
  const [document, setDocument] = useState<CorpusDocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void Promise.all([params, searchParams]).then(([route, query]) => {
      if (!active) return;
      setDocumentId(route.id);
      setVersion(query.version);
      setSection(query.section);
    });
    return () => {
      active = false;
    };
  }, [params, searchParams]);

  useEffect(() => {
    if (!documentId) return;
    let active = true;
    void getCorpusDocument("/api", documentId, version)
      .then((result) => {
        if (active) setDocument(result);
      })
      .catch((cause: unknown) => {
        if (active) {
          setError(cause instanceof ApiError ? cause.message : "Could not load the policy document.");
        }
      });
    return () => {
      active = false;
    };
  }, [documentId, version]);

  useEffect(() => {
    if (!document || !section) return;
    const normalizedSection = section.trim().replace(/\s+/g, " ").toLocaleLowerCase();
    const heading = Array.from(window.document.querySelectorAll(".markdown-content h1, .markdown-content h2, .markdown-content h3, .markdown-content h4, .markdown-content h5, .markdown-content h6"))
      .find((element) =>
        element.textContent?.trim().replace(/\s+/g, " ").toLocaleLowerCase() === normalizedSection
      );
    heading?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [document, section]);

  return (
    <main className="wrap">
      <TopBar showHistory />
      <div className="route-links">
        <Link href="/corpus">← All policies</Link>
        <Link href="/">← Assistant</Link>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {!document && !error && <p role="status">Loading policy document…</p>}
      {document && (
        <>
          <header>
            <h1>{document.title}</h1>
            <p className="lede">
              {document.owner} · Version {document.version} · Effective {document.effective}
            </p>
            {document.status === "superseded" && (
              <p className="superseded-warning" role="status">This policy version is superseded.</p>
            )}
          </header>
          <article className="policy-document markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{document.content}</ReactMarkdown>
          </article>
        </>
      )}
    </main>
  );
}
