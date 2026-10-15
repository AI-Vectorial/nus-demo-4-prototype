import type { Metadata } from "next";

import History from "@/components/History";

export const metadata: Metadata = { title: "History" };
export const dynamic = "force-dynamic";

export default function HistoryPage() {
  return <History apiUrl="/api" />;
}
