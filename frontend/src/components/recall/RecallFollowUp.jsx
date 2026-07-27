import { ArrowRight } from "lucide-react";

export default function RecallFollowUp({
  question,
  onSelect,
}) {
  if (!question) {
    return null;
  }

  return (
    <article className="panel recall-follow-up-panel">
      <p className="eyebrow">Suggested Follow-up</p>
      <h3>{question}</h3>

      <button
        type="button"
        className="secondary-action"
        onClick={() => onSelect?.(question)}
      >
        <span>Use this question</span>
        <ArrowRight size={17} />
      </button>
    </article>
  );
}
