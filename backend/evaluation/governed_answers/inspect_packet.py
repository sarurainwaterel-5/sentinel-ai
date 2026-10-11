"""Check packet integrity only. A valid packet never authorizes release.

No application imports, benchmark invocation, secrets, model clients or network.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).with_name("release_manifest.json")


def inspect_packet(root: Path, manifest: dict) -> dict:
    errors = []
    if manifest.get("production_enabled") is not False or manifest.get("semantic_grounding_verified") is not False:
        errors.append("invalid_disabled_invariants")
    if manifest.get("release_authorized") is not False or manifest.get("proposition_to_inference") != "closed":
        errors.append("invalid_authority_invariants")
    bindings = manifest.get("sha256_bindings")
    if not isinstance(bindings, dict) or not bindings:
        errors.append("missing_source_bindings")
        bindings = {}
    for name, expected in bindings.items():
        path = Path(name)
        allowed = name.startswith(("backend/app/", "backend/tests/", "backend/evaluation/", "frontend/src/", "docs/"))
        if path.is_absolute() or not allowed or ".." in path.parts or not (root / path).resolve().is_relative_to(root.resolve()):
            errors.append("invalid_binding_path")
            continue
        try:
            actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
        except OSError:
            errors.append(f"missing_binding:{name}")
            continue
        if actual != expected:
            errors.append(f"changed_binding:{name}")
    return {"packet_integrity": "invalid" if errors else "valid", "errors": errors,
        "release_authorized": False, "production_enabled": False,
        "semantic_grounding_verified": False, "proposition_to_inference": "closed",
        "release_blockers": manifest.get("release_blockers", [])}


def main():
    report = inspect_packet(ROOT, json.loads(PACKET.read_text()))
    print(json.dumps(report, indent=2))
    return 0 if report["packet_integrity"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
