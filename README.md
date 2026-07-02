# SentinelAI

> **The Knowledge Operating System for AI-First Organizations**

SentinelAI is a modular AI platform that transforms documents into organizational intelligence.

Rather than functioning as a traditional chatbot or document repository, SentinelAI ingests, organizes, retrieves, reasons over, and continuously improves institutional knowledge through domain-driven AI services.

---

## Vision

Every organization has knowledge. Very few have intelligence.

SentinelAI bridges that gap by providing a Knowledge Operating System for domain-specific AI across engineering, legal, market, business, and operational knowledge.

---

## Current Project Status

**Current Sprint:** Sprint 6.4 — Knowledge Analytics  
**Current Focus:** Knowledge Dashboard  
**Architecture Status:** Modular Monolith, Microservice Ready  
**Development Stage:** Engineering Foundation Complete  
**Next Milestone:** React Knowledge Dashboard

---

## Platform Architecture

```text
                    SentinelAI Platform

                      React Frontend
                             │
                             ▼
                     FastAPI Backend
                             │
      ┌──────────────────────┼──────────────────────┐
      ▼                      ▼                      ▼
Upload Service        Knowledge Management   Reasoning Engine
      │                      │                      │
      ▼                      ▼                      ▼
Fingerprint Service   Knowledge Analytics   Retrieval Service
      │                      │                      │
      └──────────────────────┼──────────────────────┘
                             ▼
                    PostgreSQL Metadata
                             │
                             ▼
                     Qdrant Vector Store
                             │
                             ▼
                      OpenAI Reasoning
Core Capabilities

Knowledge Ingestion

PDF processing
SHA-256 fingerprinting
Duplicate detection
Metadata catalog
Semantic chunking
Embedding generation


Knowledge Retrieval

Semantic search
Grounded RAG
Source citations
Context construction
Confidence-based retrieval


Knowledge Management

Knowledge catalog
Archive
Restore
Document metadata
Lifecycle management


Knowledge Analytics

Dashboard API
Knowledge domain statistics
Topic analytics
Collection analytics
Recent knowledge activity


Technology Stack

Backend
FastAPI
SQLAlchemy
Alembic
PostgreSQL
Qdrant
OpenAI API


Frontend

React
Vite


AI

Local sentence-transformer embeddings
GPT reasoning through OpenAI API


Engineering Philosophy

SentinelAI is developed using an architecture-first approach.

Engineering principles include:

Architecture First
Domain-Driven Design
Service-Oriented Design
Repository Pattern
Thin API Routes
API Contracts with Pydantic
Clean Git History
Architecture Decision Records
Sprint Documentation
Microservice-Ready Boundaries
Engineering Maturity

✅ Layered Architecture
✅ Repository Pattern
✅ Service Layer
✅ API Contracts
✅ Database Migrations
✅ Knowledge Catalog
✅ Duplicate Detection
✅ Grounded RAG
✅ Knowledge Analytics
🚧 React Dashboard
🚧 AI Classification
🚧 Knowledge Graph
🚧 Multi-Tenant Organizations

Development Workflow

Architecture Review
        ↓
Implementation
        ↓
Testing
        ↓
Refactoring
        ↓
Clean Git Commit
        ↓
Sprint Documentation
        ↓
Architecture Decision Record
        ↓
Update Architecture
        ↓
Next Sprint


Roadmap

Completed

Grounded RAG
Semantic Search
OpenAI Reasoning
PostgreSQL Knowledge Catalog
Document Fingerprinting
Duplicate Detection
Knowledge Management
Knowledge Analytics
Dashboard API

In Progress
React Knowledge Dashboard

Planned

AI Classification Engine
Knowledge Graph
Knowledge Coverage Analysis
Versioning
Organizations
Authentication
Multi-Agent Framework
Engineering Intelligence
Legal Intelligence
Market Intelligence
Business Intelligence

Documentation

docs/
├── architecture/
├── architecture/decisions/
├── sprints/
├── roadmap/
└── diagrams/

Long-Term Vision

SentinelAI is being engineered as a modular Knowledge Operating System capable of scaling from a single local deployment to a distributed enterprise platform supporting multiple AI-powered knowledge domains.

The goal is not simply to answer questions.

The goal is to help organizations transform knowledge into operational intelligence.


-by C.Titus-El aka Saru El
