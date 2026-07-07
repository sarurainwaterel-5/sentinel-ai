from app.core.canon.manifest import build_canon_manifest
from app.core.canon.report import build_canon_report


def build_living_canon():
    """
    Build SentinelAI's Living Canon.
    """

    manifest = build_canon_manifest()
    report = build_canon_report()

    return {
        "manifest": manifest,
        "report": report,
    }
