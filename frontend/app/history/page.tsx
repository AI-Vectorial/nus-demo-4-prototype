"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { ApiError, listConversations } from "@/lib/api";
import type { ConversationPage } from "@/lib/types";

const PAGE_SIZE = 20;

export default function HistoryPage() {
  const [page, setPage] = useState<ConversationPage | null>(null);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    void listConversations("/api", PAGE_SIZE, offset)
      .then((result) => {
        if (active) setPage(result);
      })
      .catch((cause: unknown) => {
        if (active) {
          setError(cause instanceof ApiError ? cause.message : "Could not load conversation history.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [offset]);

  return (
    <main className="wrap">
      <TopBar showHistory />
      <header>
        <h1>Conversation history</h1>
        <p className="lede">Open a saved conversation to review it or continue asking.</p>
      </header>
      <section className="history-list" aria-label="Saved conversations">
        {loading && <p role="status">Loading conversation history…</p>}
        {error && <p className="error" role="alert">{error}</p>}
        {!loading && !error && page?.total === 0 && (
          <p className="dim">No conversations yet.</p>
        )}
        {page?.conversations.map((conversation) => (
          <Link
            className="history-item"
            href={`/history/${encodeURIComponent(conversation.id)}`}
            key={conversation.id}
          >
            <strong>{conversation.preview || "Conversation"}</strong>
            <span>{new Date(conversation.last_at).toLocaleString()}</span>
            <span>{conversation.turns} {conversation.turns === 1 ? "turn" : "turns"}</span>
          </Link>
        ))}
      </section>
      {page && page.total > PAGE_SIZE && (
        <nav className="pagination" aria-label="History pages">
          <button
            type="button"
            disabled={offset === 0 || loading}
            onClick={() => {
              setLoading(true);
              setError(null);
              setOffset(Math.max(0, offset - PAGE_SIZE));
            }}
          >
            Previous
          </button>
          <span>
            {offset + 1}–{Math.min(offset + PAGE_SIZE, page.total)} of {page.total}
          </span>
          <button
            type="button"
            disabled={offset + PAGE_SIZE >= page.total || loading}
            onClick={() => {
              setLoading(true);
              setError(null);
              setOffset(offset + PAGE_SIZE);
            }}
          >
            Next
          </button>
        </nav>
      )}
    </main>
  );
}
