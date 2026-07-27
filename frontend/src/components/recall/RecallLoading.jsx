import { Sparkles } from "lucide-react";

export default function RecallLoading() {
  return (
    <section className="panel recall-loading-panel">
      <Sparkles size={22} />

      <div>
        <p className="eyebrow">
          Memory Reconstruction
        </p>

        <h3>
          Sentinel is recalling what it knows...
        </h3>

        <p className="muted">
          Searching semantic memory, assembling evidence,
          and constructing a grounded response.
        </p>
      </div>
    </section>
  );
}
