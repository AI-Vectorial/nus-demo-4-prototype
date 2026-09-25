"use client";

/**
 * The frame every route is built inside: a top bar, then the route. REQ-U9.
 *
 * The bar carries the product name and exactly two actions -- Reset and
 * Corpus. There is no rail, so there is no collapsed state, no overlay and no
 * hamburger to manage on three routes and at two widths; the same one row
 * works at every width, which is most of why the rail is gone.
 *
 * Reset is a button on the assistant, where there is a conversation in memory
 * to clear, and a link everywhere else, where returning to "/" mounts a fresh
 * one. Same word, same place, same outcome.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

export default function Shell({
  onReset,
  children,
}: {
  /** Supplied by the assistant, which holds the conversation. */
  onReset?: () => void;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const onCorpus = pathname.startsWith("/corpus");

  return (
    <div className="shell">
      <header className="topbar">
        <Link href="/" className="brand">
          Policy Assistant
        </Link>

        <nav className="topbar-actions" aria-label="Main">
          {onReset ? (
            <button type="button" className="bar-action" onClick={onReset}>
              Reset
            </button>
          ) : (
            <Link href="/" className="bar-action">
              Reset
            </Link>
          )}

          <Link
            href="/corpus"
            className={onCorpus ? "bar-action current" : "bar-action"}
            aria-current={onCorpus ? "page" : undefined}
          >
            Corpus
          </Link>
        </nav>
      </header>

      <main className="main">{children}</main>
    </div>
  );
}
