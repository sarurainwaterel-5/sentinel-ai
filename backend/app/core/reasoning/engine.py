"""
Reasoning Engine

The Engine orchestrates Reasoning.

The Engine coordinates the Builder, Validator, and Renderer to
produce accountable reasoning artifacts.

Engines orchestrate.

Engines never redefine meaning.

Engines never reorganize models.

Engines never validate directly.

Engines never render directly.

The Engine coordinates constitutional components while remaining
accountable to reality.
"""
from typing import Any

from app.core.reasoning.builder import build_reasoning_registry
from app.core.reasoning.renderer import (
    render_reasoning_narrative,
    render_reasoning_registry,
)
from app.core.reasoning.validator import (
    validate_reasoning_registry,
)

def orchestrate_reasoning(**kwargs: Any) -> dict[str, Any]:
    """
    Execute one complete constitutional reasoning cycle.

    Pipeline

        Builder
            ↓
        Validator
            ↓
        Renderer

    The Engine never bypasses constitutional boundaries.
    """

    registry = build_reasoning_registry(**kwargs)

    validate_reasoning_registry(registry)

    return {
        "registry": render_reasoning_registry(registry),
        "narrative": render_reasoning_narrative(registry),
    }

