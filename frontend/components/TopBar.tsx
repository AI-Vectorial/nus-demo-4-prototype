"use client";

/**
 * The top bar, on every route. REQ-U9: the product name, and exactly three
 * actions -- Reset, History, Corpus. No sidebar, no hamburger, no settings.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";

/** Heard by the assistant page, which drops its conversation. */
export const RESET_EVENT = "policy-assistant:reset";

export default function TopBar() {
  const router = useRouter();

  // The conversation lives in the assistant page. Tell it to drop it, then go
  // there -- from another route that mounts a fresh page anyway. The next
  // question starts a new conversation (criterion 30).
  const reset = () => {
    window.dispatchEvent(new Event(RESET_EVENT));
    router.push("/");
  };

  return (
    <header className="topbar">
      <Link href="/" className="brand">
        Policy Assistant
      </Link>
      <nav className="actions" aria-label="Main">
        <button type="button" onClick={reset}>
          Reset
        </button>
        <Link href="/history">History</Link>
        <Link href="/corpus">Corpus</Link>
      </nav>
    </header>
  );
}
