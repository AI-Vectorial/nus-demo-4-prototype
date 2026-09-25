/**
 * When the corpus cannot support an answer. F3.
 *
 * REQ-U5: a refusal must look different from an answer AND different from an
 * error. It is not a failure -- it is the product working correctly, and it is
 * the behaviour the brief says we would defend hardest. Hence a dashed card
 * rather than a red one, and a closing line that reads as the product working.
 *
 * D5 -- what a refusal says -- belongs to the backend, which sends it as the
 * `answer` field. This splits that text rather than writing its own: the first
 * paragraph leads, the last points somewhere, and nothing is invented in
 * between. When the backend sends a single paragraph, the pointer below falls
 * back to the corpus, which lists the owning team for every document.
 */

import Link from "next/link";

export default function Refusal({ reason }: { reason: string }) {
  const parts = reason
    .split(/\n\s*\n/)
    .map((part) => part.trim())
    .filter(Boolean);

  const lead = parts[0] ?? "The policy corpus does not cover this question.";
  const next = parts.length > 1 ? parts[parts.length - 1] : null;
  const middle = parts.slice(1, next === null ? undefined : -1);

  return (
    <>
      <div className="refusal">
        <p className="lead">{lead}</p>
        {middle.map((para, index) => (
          <p key={index}>{para}</p>
        ))}
        <p className="next">
          {next ?? (
            <>
              Every policy in the <Link href="/corpus">corpus</Link> lists the team
              that owns it.
            </>
          )}
        </p>
      </div>
      <p className="no-answer">No answer was generated.</p>
    </>
  );
}
