"use client";

import Link from "next/link";

export default function TopBar({
  onReset,
  showHistory = false,
}: {
  onReset?: () => void;
  showHistory?: boolean;
}) {
  return (
    <nav className="topbar" aria-label="Main navigation">
      <Link className="brand" href="/">Policy Assistant</Link>
      <div className="topbar-actions">
        {showHistory && <Link href="/history">History</Link>}
        <Link href="/corpus">Corpus</Link>
        {onReset ? (
          <button className="reset" type="button" onClick={onReset}>Reset</button>
        ) : (
          <Link className="reset" href="/">Reset</Link>
        )}
      </div>
    </nav>
  );
}
