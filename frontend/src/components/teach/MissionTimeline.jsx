const steps = [
  "Reading document",
  "Understanding structure",
  "Creating memories",
  "Connecting ideas",
  "Updating Bridge",
];

export default function MissionTimeline() {
  return (
    <section className="panel">
      <h2>Mission Timeline</h2>

      <div className="timeline">
        {steps.map((step, index) => (
          <div className="timeline-step" key={step}>
            <span className="timeline-dot">{index + 1}</span>
            <span>{step}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
