"use client";

/**
 * One policy document. F7, REQ-B3 and REQ-B4.
 *
 * Sections down the left, text beside them -- so a reader who arrived from a
 * citation can find the section it named without scrolling the whole policy.
 *
 * The text is Markdown (REQ-U12). Rendering it as markup is not decoration:
 * the tables are where the thresholds, the caps and the retention periods
 * live, and as raw pipes and dashes they cannot be read at all.
 */

import Link from "next/link";
import { useEffect, useState } from "react";

import Shell from "./Shell";
import StatusBadge from "./StatusBadge";
import { ArrowLeftIcon } from "./Icons";
import { ApiError, getCorpusDocument } from "@/lib/api";
import { formatEffective, sectionSlug } from "@/lib/format";
import Markdown from "@/lib/markdown";
import type { CorpusDocument } from "@/lib/types";

export default function CorpusDocumentView({
  apiUrl,
  id,
  version,
}: {
  apiUrl: string;
  id: string;
  version?: string;
}) {
  const [doc, setDoc] = useState<CorpusDocument | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    getCorpusDocument(apiUrl, id, version)
      .then((result) => {
        if (live) setDoc(result);
      })
      .catch((cause: unknown) => {
        if (!live) return;
        setError(
          cause instanceof ApiError ? cause.message : "Could not load the document.",
        );
      });
    return () => {
      live = false;
    };
  }, [apiUrl, id, version]);

  // The section rail follows the reader as well as leading them: an anchor
  // that only highlights on click goes stale the moment anyone scrolls.
  useEffect(() => {
    if (!doc) return;

    const slugs = doc.sections.map((section, index) =>
      sectionSlug(section.heading, index),
    );
    const elements = slugs
      .map((slug) => window.document.getElementById(slug))
      .filter((element): element is HTMLElement => element !== null);
    if (elements.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const topmost = entries
          .filter((entry) => entry.isIntersecting)
          .sort(
            (a, b) => a.boundingClientRect.top - b.boundingClientRect.top,
          )[0];
        if (topmost) setActive(topmost.target.id);
      },
      { rootMargin: "0px 0px -65% 0px" },
    );
    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, [doc]);

  // Before anything has scrolled, the first section is the one being read.
  // Derived rather than seeded into state, so the effect above stays a
  // subscription and nothing re-renders just to pick a default.
  const activeSlug =
    active ??
    (doc && doc.sections.length > 0 ? sectionSlug(doc.sections[0].heading, 0) : null);

  return (
    <Shell>
      <div className="page-scroll">
        <div className="doc-frame">
          {/* REQ-B6. An arrow and the word, back to the list it came from. */}
          <Link href="/corpus" className="back-link">
            <ArrowLeftIcon />
            Back
          </Link>

          <div className="page-head">
            <div className="page-head-row">
              <h1 className="page-title">{doc ? doc.title : "Document"}</h1>
              {doc && <StatusBadge status={doc.status} />}
            </div>
            {doc && (
              <p className="page-sub">
                {doc.owner} · v{doc.version} · effective{" "}
                {formatEffective(doc.effective)}
              </p>
            )}
          </div>

          {error && <p className="error-line">{error}</p>}
          {!error && !doc && <p className="pending">Loading the document…</p>}

          {doc && (
            <div className="doc-layout">
              <nav className="section-rail" aria-label="Sections">
                <ul>
                  {doc.sections.map((section, index) => {
                    const slug = sectionSlug(section.heading, index);
                    return (
                      <li key={slug}>
                        <a
                          href={`#${slug}`}
                          className={
                            slug === activeSlug ? "section-link active" : "section-link"
                          }
                          aria-current={slug === activeSlug ? "true" : undefined}
                          onClick={() => setActive(slug)}
                        >
                          {section.heading}
                        </a>
                      </li>
                    );
                  })}
                </ul>
              </nav>

              <article className="doc-text">
                {doc.sections.map((section, index) => {
                  const slug = sectionSlug(section.heading, index);
                  return (
                    <section key={slug} id={slug}>
                      <h2>{section.heading}</h2>
                      <Markdown text={section.text} />
                    </section>
                  );
                })}
              </article>
            </div>
          )}
        </div>
      </div>
    </Shell>
  );
}
