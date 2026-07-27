export default function RecallNextStep({
  nextStep,
}) {
  if (!nextStep) {
    return null;
  }

  return (
    <article className="panel recall-next-step-panel">
      <p className="eyebrow">
        Recommended Next Step
      </p>

      <h3>Continue the mission</h3>

      <p>{nextStep}</p>
    </article>
  );
}
