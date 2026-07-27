import { useState } from "react";

import RecallAnswer from "../components/recall/RecallAnswer";
import RecallConfidence from "../components/recall/RecallConfidence";
import RecallEvidence from "../components/recall/RecallEvidence";
import RecallFollowUp from "../components/recall/RecallFollowUp";
import RecallLoading from "../components/recall/RecallLoading";
import RecallNextStep from "../components/recall/RecallNextStep";
import RecallQuestion from "../components/recall/RecallQuestion";
import RecallTopics from "../components/recall/RecallTopics";
import RecallWorkspaceCard from "../components/recall/RecallWorkspaceCard";
import RecallEmpty from "../components/recall/RecallEmpty";

import { useDomain } from "../context/useDomain";
import { recallKnowledge } from "../services/recallApi";

export default function Recall() {
  const { activeDomain } = useDomain();

  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isRecalling, setIsRecalling] = useState(false);

  async function handleRecall(event) {
    event.preventDefault();

    if (!question.trim()) {
      setError(
        "Ask Sentinel what you want it to remember."
      );
      return;
    }

    try {
      setError(null);
      setResult(null);
      setIsRecalling(true);

      const response = await recallKnowledge({
        question,
        domainId: activeDomain?.id ?? "all",
      });

      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Sentinel could not recall knowledge."
      );
    } finally {
      setIsRecalling(false);
    }
  }

  return (
    <section className="recall-workspace">

      <RecallQuestion
        question={question}
        setQuestion={setQuestion}
        activeDomain={activeDomain}
        isRecalling={isRecalling}
        onSubmit={handleRecall}
        error={error}
      />

      {isRecalling && (
        <RecallLoading />
      )}

      {!isRecalling && !result && (
        <RecallEmpty />
      )}

      {result && (
        <section className="recall-report">

          <RecallWorkspaceCard
            activeDomain={activeDomain}
            result={result}
          />

          <RecallAnswer
            answer={result.answer}
            domainLabel={
              result.module ??
              activeDomain?.name ??
              "All Domains"
            }
          />

          <RecallConfidence
            confidence={result.confidence}
            sourceCount={
              result.sources?.length ?? 0
            }
          />

          <div className="recall-report-grid">

            <RecallNextStep
              nextStep={
                result.recommended_next_step
              }
            />

            <RecallFollowUp
              question={
                result.suggested_follow_up
              }
              onSelect={(followUp) => {
                setQuestion(followUp);

                window.scrollTo({
                  top: 0,
                  behavior: "smooth",
                });
              }}
            />

          </div>

          <RecallTopics
            topics={
              result.related_knowledge
            }
          />

          <article className="panel">

            <RecallEvidence
              sources={result.sources}
            />

          </article>

        </section>
      )}

    </section>
  );
}
