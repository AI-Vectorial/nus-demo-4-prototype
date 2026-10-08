/**
 * REQ-U9: on every route, offering only what exists. Reset always; Corpus
 * since F7; History when F8 lands, and not before.
 */

import Link from "next/link";

export default function TopBar({ onReset }: { onReset?: () => void }) {
  return (
    <nav className="topbar">
      <Link href="/" className="brand">
        Policy Assistant
      </Link>
      <div className="actions">
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
