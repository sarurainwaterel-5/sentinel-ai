import { useState } from "react";
import { useDomain } from "../context/useDomain";
import { useWorkspaceData } from "../components/workspaces/useWorkspaceData";
import {
  ResourceState,
  WorkspaceHeader,
} from "../components/workspaces/WorkspaceParts";
import DomainCard from "../components/domains/DomainCard";
import DomainSummary from "../components/domains/DomainSummary";
import DomainValidation from "../components/domains/DomainValidation";

export default function Domains({ onNavigate }) {
  const {
    domainModel,
    activeDomain,
    selectDomain,
    refreshDomains,
    domainError,
    isLoadingDomains,
  } = useDomain();
  const memory = useWorkspaceData("/domains/memory");
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState("all");
  const domains = [
    ...(domainModel?.system_domains ?? []),
    ...(domainModel?.user_domains ?? []),
  ];
  const visible = domains.filter(
    (domain) =>
      (kind === "all" || domain.kind === kind) &&
      `${domain.name} ${domain.description}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  function refresh() {
    refreshDomains();
    memory.refresh();
  }
  function enter(domainId, page) {
    selectDomain(domainId);
    onNavigate?.(page);
  }
  const registry = {
    data: domainModel,
    error: domainError,
    loading: isLoadingDomains,
    refresh: refreshDomains,
  };
  return (
    <div className="page workspace-page domains-workspace">
      <WorkspaceHeader
        title="One identity, distinct knowledge contexts"
        description="Choose a domain to scope teaching, retrieval, reasoning, and memory governance. Architecture maturity and stored knowledge are reported separately."
        onRefresh={refresh}
        loading={isLoadingDomains || memory.loading}
      />
      <section className="panel domain-scope">
        <div>
          <p className="eyebrow">Current knowledge scope</p>
          <h2>{activeDomain?.name ?? "All Domains"}</h2>
          <p className="muted">
            Your selection carries across Sentinel’s workspaces.
          </p>
        </div>
        <button
          className="secondary-action"
          onClick={() => selectDomain("all")}
          disabled={activeDomain?.id === "all"}
        >
          Use All Domains
        </button>
      </section>
      <ResourceState resource={registry} label="domain registry">
        <div className="workspace-toolbar">
          <label className="workspace-search">
            Find a domain
            <input
              type="search"
              placeholder="Search names or descriptions"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <label>
            Domain type
            <select
              aria-label="Domain type"
              value={kind}
              onChange={(event) => setKind(event.target.value)}
            >
              <option value="all">All types</option>
              <option value="system">System domains</option>
              <option value="user">User domains</option>
            </select>
          </label>
        </div>
        <ResourceState resource={memory} label="domain memory">
          <p className="muted">
            Memory observed{" "}
            {memory.data?.observed_at
              ? new Date(memory.data.observed_at).toLocaleString()
              : "at an unreported time"}{" "}
            · default organization
          </p>
        </ResourceState>
        <section className="domain-grid" aria-label="Operational domains">
          {visible.map((domain) => (
            <DomainCard
              key={domain.domain_id}
              domain={domain}
              memory={
                memory.data
                  ? (memory.data.domains[domain.domain_id] ?? {
                      indexed_documents: 0,
                      archived_documents: 0,
                      indexed_chunks: 0,
                      other_documents: 0,
                    })
                  : null
              }
              current={activeDomain?.id === domain.domain_id}
              onSelect={() => selectDomain(domain.domain_id)}
              onEnter={(page) => enter(domain.domain_id, page)}
            />
          ))}
        </section>
        {!visible.length && (
          <section className="panel">
            <h2>No matching domains</h2>
            <p className="muted">
              Change the search or type filter. User-created domain registration
              is not available in this release.
            </p>
            <button
              className="secondary-action"
              onClick={() => {
                setQuery("");
                setKind("all");
              }}
            >
              Clear filters
            </button>
          </section>
        )}
        <details>
          <summary>Registry maturity and structural validation</summary>
          <div className="workspace-grid">
            <DomainSummary summary={domainModel?.summary} />
            <DomainValidation validation={domainModel?.validation} />
          </div>
          <p className="muted">
            These checks validate the registered domain structure. They do not
            certify document coverage, semantic accuracy, or permission to act.
          </p>
        </details>
        <details>
          <summary>How domain memory is measured</summary>
          <p className="muted">
            {memory.data?.basis ??
              "Memory counts are observed from the document catalog in the default organization. Architecture references are separate from taught PDFs."}
          </p>
          <p className="muted">
            Selecting a domain changes your knowledge scope; it does not
            activate a capability or change its registered maturity.
          </p>
        </details>
      </ResourceState>
    </div>
  );
}
