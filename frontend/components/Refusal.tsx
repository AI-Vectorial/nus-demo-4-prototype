/**
 * When the corpus cannot support an answer. F3.
 *
 * SHELL -- renders nothing until you implement it.
 *
 * REQ-U5: a refusal must look different from an answer AND different from an
 * error. It is not a failure -- it is the product working correctly, and it is
 * the behaviour the brief says we would defend hardest.
 *
 * D5 is yours: what it says. "I don't know" is not enough; the user needs to
 * know where to go instead.
 */

export default function Refusal({ reason }: { reason: string }) {
  void reason;
  return null;
}
