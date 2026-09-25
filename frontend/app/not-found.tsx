import Link from "next/link";

/**
 * Our own 404.
 *
 * Next ships a default one with its own styles, and those carry a
 * prefers-color-scheme rule -- so a mistyped URL in a light-only product
 * arrived as a black page. This is the only reason this file exists.
 */
export default function NotFound() {
  return (
    <main className="notfound">
      <h1>That page does not exist</h1>
      <p>
        The assistant answers at <Link href="/">the home page</Link>, and the
        policy documents are in <Link href="/corpus">the corpus</Link>.
      </p>
    </main>
  );
}
