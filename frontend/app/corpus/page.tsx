import type { Metadata } from "next";

import CorpusList from "@/components/CorpusList";

export const metadata: Metadata = { title: "Corpus" };
export const dynamic = "force-dynamic";

export default function CorpusPage() {
  return <CorpusList apiUrl="/api" />;
}
