export default function RecallTopics({
  topics = [],
}) {
  if (!topics.length) {
    return null;
  }

  return (
    <article className="panel recall-topics-panel">
      <p className="eyebrow">Related Knowledge</p>
      <h3>Knowledge Connections</h3>

      <div className="recall-topic-list">
        {topics.map((topic) => (
          <span
            className="recall-topic-chip"
            key={topic}
          >
            {topic}
          </span>
        ))}
      </div>
    </article>
  );
}
