export default function ReflectionCard({ canonHealth }) {
  return (
    <section className="panel reflection-card">
      <p className="eyebrow">Reflection</p>
      <h2>I understand myself through {canonHealth.documents} principle documents.</h2>
      <p>
        My understanding is organized across {canonHealth.layers} knowledge layers.
        No structural inconsistencies have been detected.
      </p>
    </section>
  );
}
