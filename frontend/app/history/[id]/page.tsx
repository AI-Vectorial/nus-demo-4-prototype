import type { Metadata } from "next";

import Chat from "@/components/Chat";

export const metadata: Metadata = { title: "Conversation" };
export const dynamic = "force-dynamic";

/** A past conversation, opened from History. The reader can carry on from it (REQ-C9). */
export default async function ConversationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <Chat apiUrl="/api" initialConversationId={id} />;
}
