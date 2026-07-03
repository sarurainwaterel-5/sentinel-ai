export default function RecentDocuments({ documents }) {
  return (
    <section className="panel">
      <h2>Recent Knowledge</h2>
      {documents.map((doc) => (
        <div className="row" key={doc.id}>
          <span>{doc.filename}</span>
          <strong>{doc.status}</strong>
        </div>
      ))}
    </section>
  );
}
