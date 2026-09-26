import CorpusDocumentView from "@/components/CorpusDocumentView";

export const dynamic = "force-dynamic";

export default async function CorpusDocumentPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ version?: string; section?: string }>;
}) {
  const { id } = await params;
  // Two versions of the travel policy share one id. Without this the
  // superseded card opens the current document and silently shows the wrong
  // numbers -- the failure the corpus browser exists to prevent.
  const { version, section } = await searchParams;
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  return (
    <CorpusDocumentView apiUrl={apiUrl} id={id} version={version} section={section} />
  );
}
