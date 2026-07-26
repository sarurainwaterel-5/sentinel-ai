import { useState } from "react";
import { Search } from "lucide-react";

import { useDomain } from "../context/useDomain";
import { recallKnowledge } from "../services/recallApi";


export default function Recall() {
  const { activeDomain } = useDomain();

  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [isRecalling, setIsRecalling] = useState(false);
  const [error, setError] = useState(null);

  const handleRecall = async (event) => {
    event.preventDefault();

    if (!question.trim()) {
      setError("Ask Sentinel what you want it to remember.");
      return;
    }

    try {
      setIsRecalling(true);
      setError(null);
      setResult(null);

      const response = await recallKnowledge({
        question,
        domainId: activeDomain?.id ?? "all",
      });

      setResult(response);
    } catch (recallError) {
      setError(
        recallError instanceof Error
          ? recallError.message
          : "Sentinel could not recall knowledge.",
      );
    } finally {
      setIsRecalling(false);
    }
  };

  return (
    <section className="recall-workspace">
      <div className="panel recall-query-panel">
        <p className="eyebrow">Evidence-Based Recall</p>

        <h2>What do you want Sentinel to remember?</h2>

        <p className="muted">
          Recall is grounded in the currently selected workspace:
          {" "}
          <strong>{activeDomain?.name ?? "All Domains"}</strong>.
        </p>

        <form onSubmit={handleRecall}>
          <label htmlFor="recall-question">
            Recall Question
          </label>

          <textarea
            id="recall-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="What is ICT market structure?"
            rows={5}
          />

          <button
            type="submit"
            className="primary-action"
            disabled={isRecalling}
          >
            <Search size={18} />

            <span>
              {isRecalling ? "Recalling..." : "Recall Knowledge"}
            </span>
          </button>
        </form>

        {error && (
          <p className="teach-status">
            {error}
          </p>
        )}
      </div>

      {result && (
        <div className="panel recall-result-panel">
          <p className="eyebrow">Sentinel Response</p>

          <h2>Recall Result</h2>

          <div className="recall-answer">
            {result.answer}
          </div>

          <div className="recall-evidence">
            <h3>Evidence</h3>

            {result.sources?.length ? (
              <ul>
                {result.sources.map((source, index) => (
                  <li
                    key={`${source.document_id ?? source.filename}-${index}`}
                  >
                    <strong>{source.filename}</strong>
                    <span>
                      Chunk {source.chunk_index}
                      {" · "}
                      Score {Number(source.score).toFixed(3)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">
                No supporting evidence was returned.
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
