"use client";

/** F8 -- past conversations, newest first (REQ-C8, REQ-U13, REQ-U14). */

import Link from "next/link";
import { useEffect, useState } from "react";

import { errorMessage, listConversations } from "@/lib/api";
import type { ConversationSummary } from "@/lib/types";

export default function History({ apiUrl }: { apiUrl: string }) {
  const [items, setItems] = useState<ConversationSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listConversations(apiUrl)
      .then(setItems)
      .catch((e: unknown) => setError(errorMessage(e)));
  }, [apiUrl]);

  return (
    <main className="page">
      <h1>History</h1>
      <p className="dim">Past conversations, newest first. Open one to read it or carry on.</p>

      {error && <p className="error-box">{error}</p>}
      {!items && !error && <p className="pending">Loading conversations…</p>}
      {items && items.length === 0 && (
        <p className="dim">No conversations yet. Ask a question to start one.</p>
      )}

      <ul className="doc-list">
        {items?.map((item) => (
          <li key={item.id}>
            <Link href={`/history/${item.id}`} className="doc-card current">
              <span className="doc-title">{item.title}</span>
              <span className="doc-meta">
                {item.message_count} turns · last active{" "}
                {new Date(item.last_at).toLocaleString("en-GB")}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
