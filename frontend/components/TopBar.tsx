/**
 * The bar across the top of every route. REQ-U9, partly.
 *
 * Reset only in this slice. History and Corpus arrive with F8 and F7 -- the
 * team's decision, recorded in tickets/T1.md: "We do not ship buttons that do
 * nothing."
 */

export default function TopBar({ onReset }: { onReset: () => void }) {
  return (
    <header className="topbar">
      <span className="product">Policy Assistant</span>
      <nav>
        <button type="button" onClick={onReset}>
          Reset
        </button>
      </nav>
    </header>
  );
}
