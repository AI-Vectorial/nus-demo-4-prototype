/**
 * The icon set. Inline SVG rather than a dependency -- five shapes do not
 * justify a package, and these inherit currentColor so the tokens in
 * globals.css keep deciding the colour.
 *
 * Every icon is decorative: the control that carries it holds the label.
 */

const base = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
  focusable: false,
};

/** The send control. Up-and-away, because the question leaves the composer. */
export function SendIcon() {
  return (
    <svg {...base} className="icon" strokeWidth={2}>
      <path d="M12 19V5M6 11l6-6 6 6" />
    </svg>
  );
}

export function ChevronRightIcon() {
  return (
    <svg {...base} className="icon">
      <path d="M9 5l7 7-7 7" />
    </svg>
  );
}

export function ArrowLeftIcon() {
  return (
    <svg {...base} className="icon">
      <path d="M19 12H5M11 6l-6 6 6 6" />
    </svg>
  );
}

export function PageIcon() {
  return (
    <svg {...base} className="icon">
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
      <path d="M9 13h6M9 17h4" />
    </svg>
  );
}

export function PersonIcon() {
  return (
    <svg {...base} className="icon">
      <circle cx="12" cy="8" r="3.4" />
      <path d="M5.5 20a6.5 6.5 0 0 1 13 0" />
    </svg>
  );
}

/** A conversation, in the history list. The shape a thread takes everywhere. */
export function ChatIcon() {
  return (
    <svg {...base} className="icon">
      <path d="M20 12a7 7 0 0 1-7 7H8l-4 3v-4.3A7 7 0 0 1 4 12a7 7 0 0 1 7-7h2a7 7 0 0 1 7 7z" />
      <path d="M9 11h6M9 14h3" />
    </svg>
  );
}
