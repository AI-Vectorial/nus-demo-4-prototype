import Chat, { type Exchange } from "@/components/Chat";
import { ApiError, conversation } from "@/lib/api";
import { apiUrl as configuredApiUrl } from "@/lib/config";
import type { ConversationDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

// The browser calls our own origin, and app/api/[...path] forwards to the real
// API from the server. Handing a client component API_URL directly would have
// it fetch localhost:8000 from the laptop, which is nothing.
const BROWSER_API = "/api";

/** A stored conversation, as the exchanges the chat shows (F8, REQ-C9). */
function exchanges(detail: ConversationDetail): Exchange[] {
  const out: Exchange[] = [];
  for (const m of detail.messages) {
    if (m.role === "user") {
      out.push({ question: m.content ?? "" });
    } else if (out.length && m.outcome) {
      out[out.length - 1].response = {
        outcome: m.outcome,
        answer: m.content,
        citations: m.citations,
        conversation_id: detail.id,
        message_id: m.id,
        latency_ms: m.latency_ms ?? 0,
      };
    }
  }
  return out;
}

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ c?: string }>;
}) {
  const { c } = await searchParams;
  if (!c) return <Chat apiUrl={BROWSER_API} />;

  // Server side: this page reads the conversation from the API directly.
  let detail: ConversationDetail;
  try {
    detail = await conversation(configuredApiUrl(), c);
  } catch (error) {
    const message =
      error instanceof ApiError && error.status === 404
        ? "That conversation could not be found."
        : "That conversation could not be loaded.";
    return <Chat apiUrl={BROWSER_API} notice={message} />;
  }
  return <Chat key={c} apiUrl={BROWSER_API} conversationId={c} initial={exchanges(detail)} />;
}
