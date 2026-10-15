"use client";

/**
 * The bar across every route (REQ-U9).
 *
 * It carries only the actions whose routes exist. Reset is always there. History
 * and Corpus are here because F8 and F7 are built. A button that goes nowhere is
 * the first thing anyone presses, so none is added before its route.
 */

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { requestReset } from "@/lib/reset";

export default function TopBar() {
  const pathname = usePathname();
  const router = useRouter();

  function reset() {
    if (pathname !== "/") {
      router.push("/");
    }
    requestReset();
  }

  return (
    <header className="topbar">
      <Link href="/" className="topbar-brand">
        Policy Assistant
      </Link>
      <nav className="topbar-actions" aria-label="Main">
        <button type="button" onClick={reset} className="topbar-reset">
          Reset
        </button>
        <Link href="/history" className="topbar-link">
          History
        </Link>
        <Link href="/corpus" className="topbar-link">
          Corpus
        </Link>
      </nav>
    </header>
  );
}
