# Sentinel self-knowledge specification

RepositoryKnowledge reads a fixed reviewed registry and bounded allowlisted source files using no-symlink file descriptors. It does not import source modules, initialize models, read environment credentials or scan arbitrary user paths. Python AST definitions and exact SHA-256 hashes bind records to implementation evidence. Documentation markers provide additional consistency checks; documentation alone is not implementation proof.

Retrieval returns curated fact text, implementation status, authorization ceiling, verification status, limitations and source citations. Snapshot returns versioned capability records and source verification metadata. Missing, changed or contradictory evidence downgrades affected capabilities to UNKNOWN/UNVERIFIED and withholds the implementation description. Authorization checkpoints run before retrieval and publication. A request-specific authorized clone prevents sharing another operator's authority.

These records establish reviewed source provenance, not empirical runtime reliability or semantic accuracy. Exact evidence versions may include a reviewed working-tree source hash relative to baseline commit. There is no automatic mutable-repository refresh. New verified changes require deliberate registry review and updated pinned evidence.
