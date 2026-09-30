import Link from "next/link";

/** A route that exists, says what is coming, and offers a way back. */
export default function ComingSoon({ title, what }: { title: string; what: string }) {
  return (
    <main className="wrap coming-soon">
      <h1>{title}</h1>
      <p className="lede">{what}</p>
      <p className="lede">Coming in the next increment.</p>
      <p>
        <Link href="/">← Back to the assistant</Link>
      </p>
    </main>
  );
}
