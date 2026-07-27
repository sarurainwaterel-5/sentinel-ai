import { Search } from "lucide-react";

export default function RecallEmpty() {
  return (
    <section className="panel recall-empty-panel">
      <Search size={28} />

      <div>
        <p className="eyebrow">
          Recall Ready
        </p>

        <h3>
          Ask a question grounded in learned knowledge.
        </h3>

        <p className="muted">
          Sentinel will return an answer together with the
          documents and chunks that support it.
        </p>
      </div>
    </section>
  );
}
