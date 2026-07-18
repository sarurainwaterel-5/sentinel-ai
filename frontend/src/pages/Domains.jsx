import { useEffect, useState } from "react";

import DomainCard from "../components/domains/DomainCard";
import DomainSummary from "../components/domains/DomainSummary";
import DomainValidation from "../components/domains/DomainValidation";
import DomainsOverview from "../components/domains/DomainsOverview";
import { getDomainModel } from "../services/domainService.js";


export default function Domains() {
  const [model, setModel] = useState(null);
  const [error, setError] = useState("");
 

  useEffect(() => {
    async function loadDomains() {
      try {
        const data = await getDomainModel();
        setModel(data);
      } catch (loadError) {
        console.error(loadError);
        setError(loadError.message);
      }
    }

    loadDomains();
  }, []);

  if (error) {
    return <div className="page">Domains unavailable: {error}</div>;
  }

  if (!model) {
    return <div className="page">Loading Domains...</div>;
  }

  return (
    <div className="page">
      <DomainsOverview summary={model.summary} />

      <div className="identity-grid">
        <DomainSummary summary={model.summary} />
        <DomainValidation validation={model.validation} />
      </div>

      <section className="domain-grid">
        {model.system_domains.map((domain) => (
          <DomainCard domain={domain} key={domain.domain_id} />
        ))}
      </section>
    </div>
  );
}
