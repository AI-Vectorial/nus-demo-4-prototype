"use client";

/**
 * The top bar. F5.
 *
 * REQ-U9: Reset is always here. History and Corpus are added to this bar only
 * when their routes exist -- an action that goes nowhere is a lie about the
 * product, so they are absent, not disabled.
 */

export default function TopBar({ onReset }: { onReset: () => void }) {
  return (
    <header className="topbar">
      <span className="brand">Policy Assistant</span>
      <nav className="topbar-actions" aria-label="Main">
        <button type="button" onClick={onReset}>
          Reset
        </button>
      </nav>
    </header>
  );
}
