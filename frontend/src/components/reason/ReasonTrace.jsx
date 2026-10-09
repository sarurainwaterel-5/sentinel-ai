export default function ReasonTrace({ trace = [] }) {
  if (!trace.length) {
    return null;
  }

  return (
    <article className="panel reason-trace">
      <p className="eyebrow">
        Reasoning Trace
      </p>

      <ol>
        {trace.map((stage, index) => (
          <li key={index}>
            <span>
              {String(index + 1).padStart(2, "0")}
            </span>

            <p>{stage}</p>
          </li>
        ))}
      </ol>

      <p className="muted">
        Recorded operational stages exposed for inspection;
        these are not hidden model chain-of-thought.
      </p>
    </article>
  );
}
