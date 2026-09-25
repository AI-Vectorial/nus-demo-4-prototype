"use client";

/**
 * The left rail. REQ-U9.
 *
 * It holds New chat and Corpus, and nothing else -- no settings page and no
 * conversation list, both explicitly out of scope in PRD section 11.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";

import { MenuIcon, PageIcon } from "./Icons";

export default function Rail({
  collapsed,
  menuOpen,
  onToggle,
  onNewChat,
}: {
  /** Narrowed to a strip once a conversation has started. */
  collapsed: boolean;
  /** Shown as an overlay at phone width, where there is no room for a strip. */
  menuOpen: boolean;
  onToggle: () => void;
  /** Omitted away from the assistant, where New chat is a link back to it. */
  onNewChat?: () => void;
}) {
  const pathname = usePathname();
  const onCorpus = pathname.startsWith("/corpus");

  // The overlay is always full width: a 56px strip floating over a phone
  // screen would cover content without offering anything to click.
  const expanded = !collapsed || menuOpen;

  const classes = ["rail"];
  if (!expanded) classes.push("collapsed");
  if (menuOpen) classes.push("menu-open");

  return (
    <nav className={classes.join(" ")} aria-label="Main">
      <div className="rail-head">
        <button
          type="button"
          className="icon-button"
          onClick={onToggle}
          aria-expanded={expanded}
          aria-label={expanded ? "Collapse the menu" : "Expand the menu"}
        >
          <MenuIcon />
        </button>
        {expanded && <span className="rail-title">Policy Assistant</span>}
      </div>

      {expanded && (
        <>
          {onNewChat ? (
            <button type="button" className="new-chat" onClick={onNewChat}>
              + New chat
            </button>
          ) : (
            <Link className="new-chat" href="/">
              + New chat
            </Link>
          )}

          <div className="rail-spacer" />

          <Link
            href="/corpus"
            className={onCorpus ? "rail-link active" : "rail-link"}
            aria-current={onCorpus ? "page" : undefined}
          >
            <PageIcon />
            Corpus
          </Link>
        </>
      )}
    </nav>
  );
}
