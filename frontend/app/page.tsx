import Chat, { type Exchange } from "@/components/Chat";
import { ApiError, conversation } from "@/lib/api";
import type { ConversationDetail } from "@/lib/types";

// Server component. It reads the API location at REQUEST time, not build time.
//
// NEXT_PUBLIC_* variables are baked into the client bundle when `next build`
// runs, so changing one means rebuilding. Reading it here instead means the
// deployment can be pointed at a different API by changing an environment
// variable and restarting -- which is what a table will expect when they change
// configuration, and what an operator expects when they roll something back.
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
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
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
