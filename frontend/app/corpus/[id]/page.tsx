import type { Metadata } from "next";

import CorpusDocument from "@/components/CorpusDocument";

export const metadata: Metadata = { title: "Corpus document" };
export const dynamic = "force-dynamic";

export default async function CorpusDocumentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <CorpusDocument apiUrl="/api" documentId={id} />;
}
