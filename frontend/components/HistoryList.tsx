"use client";

/**
 * Past conversations. F8, REQ-C8 and REQ-U13.
 *
 * Every exchange is already stored with the model, the prompt version and the
 * policy versions that answered it. Storing that and never showing it means
 * the only person who can check what the assistant said is someone with
 * database access -- which is the whole reason this screen exists.
 *
 * A row carries the first question, when the thread was last touched, and how
 * many turns it holds: enough to recognise one without opening it. It is a
 * link to the assistant rather than a reader of its own, because a
 * conversation you cannot continue is a transcript, not a conversation.
 */

import Link from "next/link";
import { useEffect, useState } from "react";

import Shell from "./Shell";
import { ArrowLeftIcon, ChatIcon, ChevronRightIcon } from "./Icons";
import { ApiError, getConversations } from "@/lib/api";
import { relativeTime } from "@/lib/format";
import type { ConversationSummary } from "@/lib/types";

export default function HistoryList({ apiUrl }: { apiUrl: string }) {
  const [conversations, setConversations] = useState<ConversationSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    getConversations(apiUrl)
      .then((result) => {
        if (live) setConversations(result);
      })
      .catch((cause: unknown) => {
        if (!live) return;
        setError(
          cause instanceof ApiError ? cause.message : "Could not load the history.",
        );
      });
    return () => {
      live = false;
    };
  }, [apiUrl]);

  const count = conversations?.length ?? 0;

  return (
    <Shell>
      <div className="page-scroll">
        <div className="page">
          {/* REQ-B6 in spirit: every route off the root offers a way back, and
              an unlabelled arrow is not one. */}
          <Link href="/" className="back-link">
            <ArrowLeftIcon />
            Back
          </Link>

          <div className="page-head">
            <h1 className="page-title">History</h1>
            <p className="page-sub">
              {conversations === null
                ? "What has been asked, and what was answered"
                : `${count} ${count === 1 ? "conversation" : "conversations"}`}
            </p>
          </div>

          {error && <p className="error-line">{error}</p>}
          {!error && conversations === null && (
            <p className="pending">Loading past conversations…</p>
          )}

          {conversations?.length === 0 && (
            <div className="history-empty">
              <p>No conversations yet.</p>
              <Link href="/">Ask the assistant a policy question</Link>
            </div>
          )}

          {conversations?.map((conversation) => (
            <Link
              key={conversation.id}
              // The assistant reads the id from the query and loads the
              // thread, so opening one lands where it can be continued.
              href={`/?conversation=${encodeURIComponent(conversation.id)}`}
              className="history-row"
            >
              <span className="thumb" aria-hidden="true">
                <ChatIcon />
              </span>
              <span className="history-body">
                <span className="history-title">{conversation.title}</span>
                <span className="history-meta">
                  {relativeTime(conversation.last_at)} ·{" "}
                  {conversation.message_count}{" "}
                  {conversation.message_count === 1 ? "message" : "messages"}
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
