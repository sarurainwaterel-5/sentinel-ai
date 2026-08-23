import { useState } from "react";

import ReasonLoading from "../components/reason/ReasonLoading";
import ReasonQuestion from "../components/reason/ReasonQuestion";
import ReasonResult from "../components/reason/ReasonResult";
import { useDomain } from "../context/useDomain";

import {
  reasonAbout,
} from "../services/reasonApi";


export default function Reason() {
  const { activeDomain } = useDomain();
  const [question, setQuestion] =
    useState("");

  const [result, setResult] =
    useState(null);

  const [error, setError] =
    useState(null);

  const [isReasoning, setIsReasoning] =
    useState(false);


  async function handleReason(event) {
    event.preventDefault();

    const normalizedQuestion =
      question.trim();

    if (!normalizedQuestion) {
      setError(
        "What should Sentinel reason about?"
      );
      return;
    }

    try {
      setError(null);
      setResult(null);
      setIsReasoning(true);

      const response = await reasonAbout({
        question: normalizedQuestion,
        workspace: "reason",
        module:
          activeDomain?.id &&
          activeDomain.id !== "all"
            ? activeDomain.id
            : null,
      });

      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Sentinel could not complete reasoning."
      );
    } finally {
      setIsReasoning(false);
    }
  }


  return (
    <section className="reason-workspace">
      <ReasonQuestion
        question={question}
        setQuestion={setQuestion}
        isReasoning={isReasoning}
        onSubmit={handleReason}
        error={error}
      />

      {isReasoning && (
        <ReasonLoading />
      )}

      {!isReasoning && result && (
        <ReasonResult
          result={result}
        />
      )}
    </section>
  );
}
