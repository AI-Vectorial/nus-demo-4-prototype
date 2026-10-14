import Link from "next/link";

import TopBar from "@/components/TopBar";
import { ApiError, corpus } from "@/lib/api";
import { apiUrl as configuredApiUrl } from "@/lib/config";

// Read at request time, like the home page: the API location is configuration.
export const dynamic = "force-dynamic";

export default async function CorpusPage() {
  const apiUrl = configuredApiUrl();
  let documents;
  try {
    documents = await corpus(apiUrl);
  } catch (error) {
    return (
      <>
        <TopBar />
        <main className="wrap">
          <p className="error">
            {error instanceof ApiError ? error.message : "Could not load the policies."}
          </p>
        </main>
      </>
    );
  }

  return (
    <>
      <TopBar />
      <main className="wrap">
        <p className="back">
          <Link href="/">← Back to the assistant</Link>
        </p>
        <h1>Policies</h1>
        <p className="lede">Every policy the assistant answers from, as written.</p>
        <ul className="documents">
          {documents.map((d) => (
            <li key={`${d.id}@${d.version}`} className={d.status === "superseded" ? "superseded" : ""}>
              <Link href={`/corpus/${encodeURIComponent(d.id)}?version=${encodeURIComponent(d.version)}`}>
                {d.title}
              </Link>
              <span className="version">v{d.version}</span>
              {d.status === "superseded" ? (
                <span className="badge">Superseded</span>
              ) : (
                <span className="dim">current</span>
              )}
              <div className="meta">
                {d.owner} · effective {d.effective}
              </div>
            </li>
          ))}
        </ul>
      </main>
    </>
  );
}
