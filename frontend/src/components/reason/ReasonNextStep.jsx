import { ArrowRight } from "lucide-react";


export default function ReasonNextStep({
  nextStep,
}) {
  if (!nextStep) {
    return null;
  }

  return (
    <article className="panel reason-next-step">
      <p className="eyebrow">
        Recommended Next Step
      </p>

      <div>
        <ArrowRight size={20} />
        <p>{nextStep}</p>
      </div>
    </article>
  );
}
