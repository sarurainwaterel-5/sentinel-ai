# SentinelAI Component Library

> *"Components are the vocabulary of the Bridge."*

---

# Purpose

The SentinelAI Component Library defines the reusable interface components that make up the Bridge.

Every component should have one clear responsibility and communicate one primary idea.

Reusable components improve consistency, reduce duplication, and strengthen the user's mental model of SentinelAI.

---

# Design Philosophy

Components are not merely visual elements.

They are cognitive building blocks.

Every component should:

- Have a single responsibility
- Be reusable
- Be predictable
- Communicate clearly
- Support understanding

---

# Layout Components

## Layout

Provides the overall page structure.

Responsibilities:

- Navigation
- Workspace layout
- Content organization

---

## Sidebar

Primary navigation for the Bridge.

Responsibilities:

- Workspace selection
- System navigation
- Identity of the current workspace

---

## TopBar

Displays the active workspace.

Responsibilities:

- Workspace title
- Context
- Orientation

---

# Dashboard Components

## Overview Cards

Summarize key operational metrics.

Examples:

- Documents
- Knowledge
- Health
- Active Missions

---

## Knowledge Domains

Visual representation of SentinelAI's knowledge organization.

---

## Recent Documents

Displays recently ingested or modified knowledge.

---

# Teach Components

## Teach Hero

Introduces the Teach workspace.

Provides mission context.

---

## Teach Drop Zone

Primary interface for teaching SentinelAI.

Supports document ingestion.

---

## Knowledge Summary

Summarizes knowledge currently available for learning.

---

## Mission Timeline

Displays recent teaching activity.

---

## Recent Missions

History of recent ingestion operations.

---

# Identity Components

## Identity Hero

Introduces SentinelAI's Identity workspace.

---

## Identity Overview

High-level summary of SentinelAI's current identity.

---

## Canon Health Card

Displays Canon status and health.

---

## Knowledge Layers

Visualizes the Living Canon's organizational structure.

---

## Reflection Card

Displays SentinelAI's current self-reflection.

---

# Future Components

The following component families are planned.

## Recall

Knowledge retrieval interface.

---

## Reason

Reasoning visualization.

---

## Systems

Operational awareness dashboard.

---

## Governance

Constitution and policy visualization.

---

## Intelligence

Cognitive engine visualization.

---

# Component Standards

Every component should:

- Have one responsibility
- Be composable
- Avoid duplicated logic
- Receive data through props
- Be independent of backend implementation
- Be reusable across workspaces

Components should communicate ideas rather than implementation details.

---

# Naming Convention

Component names should describe purpose rather than appearance.

Examples:

✅ KnowledgeLayers

✅ ReflectionCard

✅ CanonHealthCard

Avoid:

❌ BlueCard

❌ BigPanel

❌ Widget1

---

# Closing Principle

Every component exists to strengthen understanding.

Together they form the visual language of the Bridge.
