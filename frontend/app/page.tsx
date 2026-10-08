import Chat, { type Exchange } from "@/components/Chat";
import { ApiError, conversation } from "@/lib/api";
import type { ConversationDetail } from "@/lib/types";
import { apiUrl as configuredApiUrl } from "@/lib/config";

// Server component: the API location is read at request time (lib/config.ts).
export const dynamic = "force-dynamic";

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
  const apiUrl = configuredApiUrl();
  const { c } = await searchParams;
  if (!c) return <Chat apiUrl={apiUrl} />;

  let detail: ConversationDetail;
  try {
    detail = await conversation(apiUrl, c);
  } catch (error) {
    const message =
      error instanceof ApiError && error.status === 404
        ? "That conversation could not be found."
        : "That conversation could not be loaded.";
    return <Chat apiUrl={apiUrl} notice={message} />;
  }
  return <Chat key={c} apiUrl={apiUrl} conversationId={c} initial={exchanges(detail)} />;
}
