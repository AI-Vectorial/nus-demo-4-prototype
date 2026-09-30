/**
 * Something failed. REQ-U5: not an answer and not a refusal -- a solid danger
 * border and the word "Error", so nobody mistakes it for the product
 * declining a question it cannot answer.
 */

export default function ErrorNotice({ message }: { message: string }) {
  return (
    <section className="error" role="alert" aria-label="Error">
      <p className="lead">Error — no answer, and no refusal</p>
      <p>{message}</p>
      <p className="next">Try again in a moment. If it keeps happening, the service may be down.</p>
    </section>
  );
}
