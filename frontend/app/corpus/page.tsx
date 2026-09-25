import CorpusList from "@/components/CorpusList";

// Server component, same pattern as app/page.tsx: the API location is read at
// REQUEST time and handed down, so pointing a deployment at a different API is
// an environment variable and a restart, not a rebuild.
export const dynamic = "force-dynamic";

export default function CorpusPage() {
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  return <CorpusList apiUrl={apiUrl} />;
}
