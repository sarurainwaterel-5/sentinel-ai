import { useEffect, useState } from "react";
import IdentityHero from "../components/identity/IdentityHero";
import IdentityOverview from "../components/identity/IdentityOverview";
import CanonHealthCard from "../components/identity/CanonHealthCard";
import KnowledgeLayers from "../components/identity/KnowledgeLayers";
import ReflectionCard from "../components/identity/ReflectionCard";
import { getCanonHealth } from "../services/canonService";

export default function Identity() {
  const [canonHealth, setCanonHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadCanon() {
      try {
        const data = await getCanonHealth();
        setCanonHealth(data);
      } catch (error) {
        console.error(error);
        setError(error.message);
      }
    }

    loadCanon();
  }, []);

  if (error) {
    return (
      <div className="page">
        <section className="panel">
          <p className="eyebrow">Identity</p>
          <h2>Canon unavailable</h2>
          <p className="muted">{error}</p>
        </section>
      </div>
    );
  }

  if (!canonHealth) {
    return (
      <div className="page">
        <section className="panel">
          <p className="eyebrow">Identity</p>
          <h2>Loading SentinelAI Identity...</h2>
          <p className="muted">Reading the Living Canon.</p>
        </section>
      </div>
    );
  }

  const identity = {
    status: canonHealth.status ?? "unknown",
    version: "1.0",
    documents: canonHealth.document_count ?? 0,
    layers: canonHealth.layer_count ?? 0,
    architectureDecisions: canonHealth.types?.architecture_decision ?? 0,
    sprintRecords: canonHealth.types?.sprint_record ?? 0,
    warnings: canonHealth.warnings ?? [],
  };

  return (
    <div className="page">
      <IdentityHero />
      <IdentityOverview canonHealth={identity} />

      <div className="identity-grid">
        <CanonHealthCard canonHealth={identity} />
        <KnowledgeLayers layers={canonHealth.layers ?? {}} />
      </div>

      <ReflectionCard canonHealth={identity} />
    </div>
  );
}
