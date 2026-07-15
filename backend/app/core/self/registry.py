from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class EvidenceRecord:
    """
    A source that supports one or more facts in SentinelAI's self-model.
    """

    evidence_type: str
    source: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IdentityRegistry:
    """
    Facts describing what SentinelAI is and why it exists.
    """

    name: str = ""
    category: str = ""
    purpose: str = ""
    mission: str = ""
    version: str = ""
    principles: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class StructureRegistry:
    """
    Facts describing how SentinelAI is organized.
    """

    services: list[dict[str, Any]] = field(default_factory=list)
    workspaces: list[dict[str, Any]] = field(default_factory=list)
    routes: list[dict[str, Any]] = field(default_factory=list)
    knowledge_layers: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class FunctionRegistry:
    """
    Facts describing what SentinelAI can currently do and where it operates.
    """

    capabilities: list[dict[str, Any]] = field(default_factory=list)
    operational_domains: list[dict[str, Any]] = field(default_factory=list)
    workflows: list[dict[str, Any]] = field(default_factory=list)
    tools: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class KnowledgeRegistry:
    """
    Facts describing the knowledge SentinelAI currently possesses.
    """

    documents: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    knowledge_sources: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class BoundariesRegistry:
    """
    Facts describing SentinelAI's limitations, policies, and unsupported claims.
    """

    limitations: list[dict[str, Any]] = field(default_factory=list)
    policies: list[dict[str, Any]] = field(default_factory=list)
    unsupported_capabilities: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SelfRegistry:
    """
    Evidence-backed ontology of SentinelAI's current engineered state.

    The registry stores observed facts only. It does not generate prose,
    interpret evidence, or claim capabilities that have not been verified.
    """

    identity: IdentityRegistry = field(default_factory=IdentityRegistry)
    structure: StructureRegistry = field(default_factory=StructureRegistry)
    function: FunctionRegistry = field(default_factory=FunctionRegistry)
    knowledge: KnowledgeRegistry = field(default_factory=KnowledgeRegistry)
    boundaries: BoundariesRegistry = field(default_factory=BoundariesRegistry)
    evidence: list[EvidenceRecord] = field(default_factory=list)

    def add_evidence(
        self,
        evidence_type: str,
        source: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Register evidence supporting one or more facts in the self-model.
        """

        self.evidence.append(
            EvidenceRecord(
                evidence_type=evidence_type,
                source=source,
                description=description,
                metadata=metadata or {},
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Return a fully serializable representation of the registry.
        """

        return asdict(self)
