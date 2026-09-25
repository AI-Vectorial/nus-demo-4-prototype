/**
 * Current or superseded, on a corpus card or a document header. REQ-B2.
 *
 * The word itself is the signal, not the colour -- rust and jade read the same
 * to a colourblind reader, and "which version is this" is exactly the question
 * this product exists to answer.
 */

export default function StatusBadge({
  status,
}: {
  status: "current" | "superseded";
}) {
  return <span className={`pill ${status}`}>{status}</span>;
}
