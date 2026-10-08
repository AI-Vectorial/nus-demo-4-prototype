/**
 * REQ-U9: on every route, offering only what exists. Reset always; Corpus
 * since F7; History since F8.
 */

import Link from "next/link";

export default function TopBar({ onReset }: { onReset?: () => void }) {
  return (
    <nav className="topbar">
      <Link href="/" className="brand">
        Policy Assistant
      </Link>
      <div className="actions">
        <Link href="/history">History</Link>
        <Link href="/corpus">Corpus</Link>
        {onReset ? (
          <button type="button" onClick={onReset}>
            Reset
          </button>
        ) : (
          <Link href="/">Reset</Link>
        )}
      </div>
    </nav>
  );
}
