"""
Deliberation Language

Deliberation is the disciplined examination of competing possibilities
in order to identify the most responsible course of consideration while
preserving human judgment, constitutional principles, and accountability
to reality.

This module defines the canonical vocabulary governing SentinelAI's
Deliberation subsystem.

Language defines meaning.

Language precedes structure.

Language never evaluates options.

Language never makes recommendations.

Language never replaces human judgment.
"""

from typing import Final, Literal


OptionStatus = Literal[
    "candidate",
    "admissible",
    "constrained",
    "rejected",
    "preferred",
]

ConstraintStatus = Literal[
    "satisfied",
    "partially_satisfied",
    "violated",
    "unresolved",
]

RiskLevel = Literal[
    "minimal",
    "low",
    "moderate",
    "high",
    "critical",
    "unknown",
]

BenefitLevel = Literal[
    "minimal",
    "low",
    "moderate",
    "high",
    "substantial",
    "unknown",
]

ReversibilityStatus = Literal[
    "reversible",
    "partially_reversible",
    "irreversible",
    "unknown",
]

RestraintStatus = Literal[
    "not_required",
    "advisable",
    "required",
    "defer_to_human",
    "insufficient_evidence",
]

RecommendationStatus = Literal[
    "preferred",
    "conditional",
    "deferred",
    "no_acceptable_option",
    "human_decision_required",
]


DELIBERATION_DEFINITION: Final[str] = (
    "Deliberation is the disciplined examination of competing possibilities "
    "in order to identify the most responsible course of consideration while "
    "preserving human judgment, constitutional principles, and accountability "
    "to reality."
)

DELIBERATION_LAW: Final[str] = (
    "Deliberation supports responsible human choice. "
    "Deliberation does not replace human judgment."
)

POSSIBILITY_DEFINITION: Final[str] = (
    "A Possibility is a candidate path that may be considered before formal "
    "evaluation or constitutional admission."
)

OPTION_DEFINITION: Final[str] = (
    "An Option is a sufficiently structured Possibility admitted into formal "
    "deliberation."
)

VALUE_DEFINITION: Final[str] = (
    "A Value identifies a quality that should be preserved, protected, or "
    "advanced during deliberation without replacing evidence."
)

CONSTRAINT_DEFINITION: Final[str] = (
    "A Constraint defines a boundary that an Option must respect in order to "
    "remain constitutionally acceptable."
)

TRADEOFF_DEFINITION: Final[str] = (
    "A Tradeoff exists when advancing one responsible quality requires "
    "reducing, delaying, or accepting risk to another."
)

RISK_ASSESSMENT_DEFINITION: Final[str] = (
    "A Risk Assessment evaluates the likelihood, severity, exposure, "
    "detectability, reversibility, and safeguards associated with an "
    "unwanted consequence."
)

BENEFIT_ASSESSMENT_DEFINITION: Final[str] = (
    "A Benefit Assessment evaluates the reasonably supported positive "
    "consequences associated with an Option."
)

CONSEQUENCE_DEFINITION: Final[str] = (
    "A Consequence describes an intended or foreseeable effect that may "
    "follow from selecting, rejecting, or delaying an Option."
)

REVERSIBILITY_DEFINITION: Final[str] = (
    "Reversibility describes the degree to which the effects of an Option "
    "can be responsibly undone or corrected."
)

PROPORTIONALITY_DEFINITION: Final[str] = (
    "Proportionality examines whether the scope and risk of an Option are "
    "appropriate to the evidence, need, authority, and expected benefit."
)

RESTRAINT_DEFINITION: Final[str] = (
    "Restraint is the disciplined decision not to act beyond what available "
    "evidence, authority, responsibility, or constitutional boundaries can "
    "support."
)

RESTRAINT_ASSESSMENT_DEFINITION: Final[str] = (
    "A Restraint Assessment determines whether action should proceed, be "
    "delayed, require more evidence, be deferred to human authority, or not "
    "occur."
)

DELIBERATIVE_RECOMMENDATION_DEFINITION: Final[str] = (
    "A Deliberative Recommendation identifies a preferred Option, viable "
    "alternatives, governing principles, risks, benefits, tradeoffs, "
    "constraints, uncertainty, and reasons for preference."
)

DELIBERATION_REPORT_DEFINITION: Final[str] = (
    "A Deliberation Report communicates the complete constitutional record "
    "of one deliberative cycle."
)

HUMAN_AGENCY_DEFINITION: Final[str] = (
    "Human Agency is the constitutional principle that final authority over "
    "meaningful decisions and actions remains with people."
)

HUMAN_JUDGMENT_DEFINITION: Final[str] = (
    "Human Judgment is the exercise of human authority after considering "
    "evidence, reasoning, deliberative recommendations, uncertainty, and "
    "responsibility."
)

RESPONSIBLE_OPTION_DEFINITION: Final[str] = (
    "A Responsible Option is an admissible Option that respects governing "
    "constraints, preserves human agency, exposes material tradeoffs, and "
    "remains proportionate to available evidence."
)


CANONICAL_DELIBERATION_TERMS: Final[dict[str, str]] = {
    "deliberation": DELIBERATION_DEFINITION,
    "possibility": POSSIBILITY_DEFINITION,
    "option": OPTION_DEFINITION,
    "value": VALUE_DEFINITION,
    "constraint": CONSTRAINT_DEFINITION,
    "tradeoff": TRADEOFF_DEFINITION,
    "risk_assessment": RISK_ASSESSMENT_DEFINITION,
    "benefit_assessment": BENEFIT_ASSESSMENT_DEFINITION,
    "consequence": CONSEQUENCE_DEFINITION,
    "reversibility": REVERSIBILITY_DEFINITION,
    "proportionality": PROPORTIONALITY_DEFINITION,
    "restraint": RESTRAINT_DEFINITION,
    "restraint_assessment": RESTRAINT_ASSESSMENT_DEFINITION,
    "deliberative_recommendation": (
        DELIBERATIVE_RECOMMENDATION_DEFINITION
    ),
    "deliberation_report": DELIBERATION_REPORT_DEFINITION,
    "human_agency": HUMAN_AGENCY_DEFINITION,
    "human_judgment": HUMAN_JUDGMENT_DEFINITION,
    "responsible_option": RESPONSIBLE_OPTION_DEFINITION,
}
