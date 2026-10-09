import { LoaderCircle } from "lucide-react";


export default function ReasonLoading() {
  return (
    <article className="panel reason-loading" role="status">
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
          Waiting for the reasoning service to return an inspectable report.
          Processing stages will appear only when reported by the backend.
        </p>
      </div>
    </article>
  );
}
