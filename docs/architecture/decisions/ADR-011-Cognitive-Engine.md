# ADR-011: Cognitive Engine

## Status

Accepted

## Context

SentinelAI is evolving beyond a traditional backend API.

The system now contains identity, memory, knowledge, reasoning, reflection, and interface layers. Organizing these capabilities only as generic services no longer fully describes what the platform is becoming.

SentinelAI needs an architecture that reflects how intelligence flows through the system.

## Decision

SentinelAI will organize its intelligence capabilities around a Cognitive Engine.

The Cognitive Engine is responsible for coordinating:

- Identity Layer
- Knowledge Layer
- Mission Context
- Coherence Engine
- Reasoning Orchestrator
- Prompt Assembly
- Reflection
- Response Generation

The backend remains implemented as a modular monolith for now, but the internal design will follow cognitive domains instead of purely technical folders.

## Cognitive Flow

```text
Question
   ↓
Identity Layer
   ↓
Knowledge Layer
   ↓
Coherence Engine
   ↓
Reasoning Orchestrator
   ↓
Prompt Assembly
   ↓
Intelligence Model
   ↓
Reflection
   ↓
Response

Layers
Identity Layer

Defines who SentinelAI is.

Includes:

Vision
Manifesto
Principles
Builder's Oath
Language Guide
Cognitive Design Principles
Architecture Decisions
Knowledge Layer

Defines what SentinelAI knows.

Includes:

Engineering knowledge
Legal knowledge
Market knowledge
Business knowledge
Uploaded domain documents
Mission Context

Defines what SentinelAI is currently doing.

Includes:

Current question
Current workspace
Current session
Current user intent
Coherence Engine

Checks whether knowledge and recommendations align with identity.

Reasoning Orchestrator

Coordinates the reasoning workflow.

Reflection Service

Reviews the response before returning it.

Design Principle

Heart and mind must remain coherent.

Identity guides knowledge.

Knowledge expands capability.

Coherence protects trust.
