ADR-027: Constitutional Deliberation Subsystem
Status

Accepted

Context

SentinelAI had already earned the ability to acquire knowledge, construct understanding, reflect upon experience, and produce constitutionally coherent reasoning.

However, coherent reasoning alone does not prepare responsible action.

Human decision-making requires consideration of multiple admissible possibilities, competing values, operational constraints, proportionality, uncertainty, restraint, and the preservation of human agency.

A new constitutional subsystem was required to organize these responsibilities without allowing recommendations to become decisions.

Decision

SentinelAI adopts a dedicated Deliberation Subsystem responsible for constitutional deliberation.

The subsystem follows the Universal Subsystem Pattern:

Theory
    ↓
Language
    ↓
Models
    ↓
Builder
    ↓
Validator
    ↓
Renderer
    ↓
Engine

Each layer owns one responsibility and delegates all remaining responsibilities to the appropriate constitutional component.

Constitutional Responsibilities
Language

Defines the constitutional vocabulary of deliberation.

Models

Represent deliberative artifacts without performing deliberation.

Builder

Organizes deliberative structures.

Builders never evaluate.

Validator

Protects constitutional responsibility.

Validators verify structural integrity, traceability, and preservation of human agency.

Validators never deliberate.

Renderer

Communicates deliberative structures faithfully.

Renderers preserve uncertainty, tradeoffs, proportionality, restraint, and human judgment.

Engine

Coordinates Builder, Validator, and Renderer.

The Engine never performs deliberation itself.

Constitutional Principle

Recommendations remain recommendations.

SentinelAI shall never convert a recommendation into a human decision.

Human judgment remains sovereign.

Architectural Consequences

SentinelAI now supports:

Multiple admissible options
Explicit tradeoffs
Risk and benefit assessment
Proportionality analysis
Constitutional restraint
Human-decision preservation
Faithful deliberation reporting
Result

Reasoning explains.

Deliberation prepares responsibility.

Human judgment decides.
