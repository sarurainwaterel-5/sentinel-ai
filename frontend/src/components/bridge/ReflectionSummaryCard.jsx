export default function ReflectionSummaryCard({ reflection }) {
  return (
    <section className="panel reflection-card">
      <p className="eyebrow">Reflection</p>
      <h2>{reflection.status === "healthy" ? "System Coherent" : "Review needed"}</h2>
      <p>{reflection.message}</p>
    </section>
  );
}
