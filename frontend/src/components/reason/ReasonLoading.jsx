import { LoaderCircle } from "lucide-react";


export default function ReasonLoading() {
  return (
    <article className="panel reason-loading">
      <LoaderCircle
        className="reason-spinner"
        size={22}
      />

      <div>
        <p className="eyebrow">
          Cognitive Operation
        </p>

        <h3>
          Analyzing evidence
        </h3>

        <p className="muted">
          Sentinel is retrieving knowledge,
          evaluating support, and constructing
          an evidence-grounded conclusion.
        </p>
      </div>
    </article>
  );
}
