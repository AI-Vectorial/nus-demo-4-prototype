import Link from "next/link";

import Markdown from "@/components/Markdown";
import TopBar from "@/components/TopBar";
import { ApiError, policy } from "@/lib/api";
import { slug } from "@/lib/slug";

export const dynamic = "force-dynamic";

export default async function PolicyPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ version?: string }>;
}) {
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  const { id } = await params;
  const { version } = await searchParams;

  let document;
  try {
    document = await policy(apiUrl, id, version);
  } catch (error) {
    return (
      <>
        <TopBar />
        <main className="wrap">
          <p className="back">
            <Link href="/corpus">← All policies</Link> · <Link href="/">Assistant</Link>
          </p>
          <p className="error">
            {error instanceof ApiError && error.status === 404
              ? "That policy, or that version of it, is not in the corpus."
              : error instanceof ApiError
                ? error.message
                : "Could not load the policy."}
          </p>
        </main>
      </>
    );
  }

  const [intro, ...sections] = document.sections;
  const superseded = document.status === "superseded";

  return (
    <>
      <TopBar />
      <main className="wrap policy">
        <p className="back">
          <Link href="/corpus">← All policies</Link> · <Link href="/">Assistant</Link>
        </p>
        <h1>{document.title}</h1>
        <p className="meta">
          v{document.version} · {document.owner} · effective {document.effective}{" "}
          {superseded ? <span className="badge superseded-badge">Superseded</span> : null}
        </p>
        {superseded && (
          <p className="degraded">
            This version is superseded and kept for reference. It is not current guidance.
          </p>
        )}
        {intro?.text && <Markdown>{intro.text}</Markdown>}

        <nav className="toc" aria-label="Sections">
          <ul>
            {sections.map((s) => (
              <li key={s.heading} className={s.text ? "" : "group"}>
                <a href={`#${slug(s.heading)}`}>{s.heading}</a>
              </li>
            ))}
          </ul>
        </nav>

        {sections.map((s) => (
          <section key={s.heading} id={slug(s.heading)} className="policy-section">
            {s.text ? <h3>{s.heading}</h3> : <h2>{s.heading}</h2>}
            {s.text && <Markdown>{s.text}</Markdown>}
          </section>
        ))}
      </main>
    </>
  );
}
