# Constitution Builder

## Purpose

The Constitution Builder compiles SentinelAI's governing documents into protected Core Memory.

SentinelAI's Constitution is not stored manually in prompts. It is generated from version-controlled Markdown documents so it can be reviewed, rebuilt, validated, and traced through Git history.

## Source Documents

The Constitution is built from:

- docs/philosophy/
- docs/design/
- docs/architecture/decisions/

These documents define SentinelAI's:

- Vision
- Manifesto
- Principles
- Builder's Oath
- Cognitive Design
- Language
- Architecture Decisions

## Processing Flow

```text
Markdown Source Documents
        ↓
Validate Required Documents
        ↓
Read Markdown Content
        ↓
Calculate Constitution Hash
        ↓
Chunk Documents
        ↓
Generate Embeddings
        ↓
Replace sentinel_core_memory
        ↓
Return Build Report
Output

The compiled Constitution is stored in:

sentinel_core_memory

This Qdrant collection is a compiled artifact, not the source of truth.

Source of Truth

The source of truth is always the Markdown in docs/.

If the documents change, the Constitution should be rebuilt.

Build Report

A successful build should return:

Status
Constitution version
Constitution hash
Documents processed
Chunks embedded
Collection name
Validation result
Design Principle

SentinelAI's Constitution is treated as code.

It is:

Version controlled
Reviewable
Rebuildable
Validatable
Explainable
Future Governance

Future versions may support:

Proposed amendments
Constitution version history
Approval workflow
Core Memory validation
Mission Log entries
