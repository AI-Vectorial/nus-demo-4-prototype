import Link from "next/link";

import TopBar from "@/components/TopBar";
import { ApiError, conversations } from "@/lib/api";

export const dynamic = "force-dynamic";

const when = new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" });

export default async function HistoryPage() {
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  let list;
  try {
    list = await conversations(apiUrl);
  } catch (error) {
    return (
      <>
        <TopBar />
        <main className="wrap">
          <p className="error">
            {error instanceof ApiError ? error.message : "Could not load the history."}
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
        <h1>History</h1>
        {list.length === 0 ? (
          <p className="lede">No conversations yet. Ask a question and it will appear here.</p>
        ) : (
          <ul className="documents">
            {list.map((c) => (
              <li key={c.id}>
                <Link href={`/?c=${encodeURIComponent(c.id)}`}>{c.title}</Link>
                <div className="meta">
                  {when.format(new Date(c.last_at))} · {c.message_count} messages
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}
