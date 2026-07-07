from pathlib import Path

# backend/app/core/canon/discovery.py
PROJECT_ROOT = Path(__file__).resolve().parents[4]
CANON_ROOT = PROJECT_ROOT / "docs"


def discover_documents():
    """
    Discover Markdown documents that belong to the SentinelAI Canon.
    """

    return sorted(CANON_ROOT.rglob("*.md"))
