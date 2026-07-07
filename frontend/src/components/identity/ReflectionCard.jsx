export default function ReflectionCard({ canonHealth }) {
  return (
    <section className="panel reflection-card">
      <p className="eyebrow">Reflection</p>
      <h2>I understand myself through {canonHealth.documents} canonical documents.</h2>
      <p>
        These documents are organized into {canonHealth.layers} knowledge layers.
        No structural inconsistencies have been detected.
      </p>
    </section>
  );
}
