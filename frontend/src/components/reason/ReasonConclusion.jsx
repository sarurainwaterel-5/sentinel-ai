export default function ReasonConclusion({ reasoning }) {
  return (
    <article className="panel reason-conclusion">
      <p className="eyebrow">
        Supported Conclusion
      </p>

      <h2>
        {reasoning?.conclusion ??
          "No supported conclusion"}
      </h2>

      {reasoning?.evidence_summary && (
        <p className="muted">
          {reasoning.evidence_summary}
        </p>
      )}

      {reasoning?.inference_summary && (
        <section className="reason-inference">
          <p className="eyebrow">
            Inference
          </p>

          <p>
            {reasoning.inference_summary}
          </p>
        </section>
      )}
    </article>
  );
}
