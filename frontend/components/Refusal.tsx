/**
 * When the corpus cannot support an answer. F3.
 *
 * REQ-U5: different from an answer AND from an error. It is the product
 * working correctly. D5 (table 3): the text comes from the API -- fixed words
 * plus each current policy and its owner -- so the user knows where to go.
 */

export default function Refusal({ reason }: { reason: string }) {
  const [lead, ...rest] = reason.split(/\n\s*\n/);
  return (
    <div className="refusal" role="status">
      <p className="lead">{lead}</p>
      {rest.map((block, i) => {
        const lines = block.split("\n");
        return lines.every((l) => l.startsWith("- ")) ? (
          <ul key={i} className="next">
            {lines.map((l) => (
              <li key={l}>{l.slice(2)}</li>
            ))}
          </ul>
        ) : (
          <p key={i} className="next">
            {block}
          </p>
        );
      })}
    </div>
  );
}
