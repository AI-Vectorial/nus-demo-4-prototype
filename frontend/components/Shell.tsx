"use client";

/**
 * Rail plus main area. Every route is built inside one of these.
 *
 * The rail collapses to a strip on a desktop and slides away entirely on a
 * phone (REQ-U10), so the two states are separate: `collapsed` is the strip,
 * `menuOpen` is the phone overlay. One boolean cannot be both, because the
 * assistant's empty state wants the rail open on a desktop and shut on a phone.
 */

import { useState, type ReactNode } from "react";

import Rail from "./Rail";
import { MenuIcon } from "./Icons";

export default function Shell({
  collapsed,
  onToggleCollapsed,
  onNewChat,
  topbar,
  children,
}: {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onNewChat?: () => void;
  /** The topbar's contents. Omitted on the assistant's empty state. */
  topbar?: ReactNode;
  children: ReactNode;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  function toggleRail() {
    if (menuOpen) setMenuOpen(false);
    else onToggleCollapsed();
  }

  const menuButton = (
    <button
      type="button"
      className="icon-button rail-open"
      onClick={() => setMenuOpen(true)}
      aria-label="Open the menu"
      aria-expanded={menuOpen}
    >
      <MenuIcon />
    </button>
  );

  return (
    <div className="shell">
      <Rail
        collapsed={collapsed}
        menuOpen={menuOpen}
        onToggle={toggleRail}
        onNewChat={onNewChat}
      />

      {menuOpen && (
        <button
          type="button"
          className="scrim"
          onClick={() => setMenuOpen(false)}
          aria-label="Close the menu"
        />
      )}

      <main className="main">
        <header className={topbar ? "topbar" : "topbar topbar-bare"}>
          {menuButton}
          {topbar}
        </header>
        {children}
      </main>
    </div>
  );
}
