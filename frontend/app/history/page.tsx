import ComingSoon from "@/components/ComingSoon";

// F8 is outside this increment (tickets/T1.md, criterion 33).
export default function History() {
  return (
    <ComingSoon
      title="History"
      what="Past conversations, newest first — each one stored with the model, prompt version and policy versions that answered it."
    />
  );
}
