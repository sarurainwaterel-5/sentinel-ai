"""Read-only repository facts; never a semantic acceptance or execution authority.

An application supplies the trusted repository root and current authorization
checkpoint. No imports of application configuration, providers or runtime routes.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat


REGISTRY_SHA256 = "700c89c498fb8d1e64fc43e77c6a6f6ce82fff6b85de7604285a714a6243c292"
REGISTRY_PATH = Path(__file__).with_name("capability_registry.json")
MAX_FILE_BYTES = 262144
_STATUSES = frozenset({"IMPLEMENTED", "EXPERIMENTAL", "PLANNED", "DISABLED", "UNKNOWN"})


class KnowledgeError(ValueError):
    """Safe bounded errors with no filesystem or credential disclosure."""


def _read(root, relative):
    """Read bounded regular files through no-symlink directory descriptors."""
    parts = relative.split("/")
    if not parts or any(not p or p in {".", ".."} for p in parts):
        raise KnowledgeError("SOURCE_UNAVAILABLE")
    descriptors = []
    try:
        descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(descriptor)
        for part in parts[:-1]:
            descriptor = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                 dir_fd=descriptor)
            descriptors.append(descriptor)
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=descriptor)
        descriptors.append(descriptor)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
            raise KnowledgeError("SOURCE_UNAVAILABLE")
        with os.fdopen(os.dup(descriptor), "rb") as stream:
            value = stream.read(MAX_FILE_BYTES + 1)
        if len(value) > MAX_FILE_BYTES:
            raise KnowledgeError("SOURCE_UNAVAILABLE")
        return value
    except (OSError, ValueError):
        raise KnowledgeError("SOURCE_UNAVAILABLE") from None
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _registry():
    try:
        raw = _read(REGISTRY_PATH.parent, REGISTRY_PATH.name)
        if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
            raise ValueError()
        result = json.loads(raw)
        if (result["schema_version"] != "22B-capabilities-v1"
                or not 1 <= len(result["sources"]) <= 64
                or not 1 <= len(result["capabilities"]) <= 32):
            raise ValueError()
        for capability in result["capabilities"]:
            if capability["implementation_status"] not in _STATUSES:
                raise ValueError()
        return result
    except (OSError, ValueError, KeyError, TypeError):
        raise KnowledgeError("REGISTRY_UNAVAILABLE") from None


def _symbols(raw):
    tree = ast.parse(raw)
    result = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            result.add(node.name)
            if isinstance(node, ast.ClassDef):
                result.update(node.name + "." + child.name for child in node.body
                              if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)))
    return result


class RepositoryKnowledge:
    """Bounded exact-version inspection; checkpoint exceptions propagate closed.

    Authorization status is the capability's policy ceiling, not an access grant.
    authorize must recheck the actual request's issued user/application authority.
    The trusted process, registry code and local filesystem owner are boundaries.
    """
    def authorized(self, checkpoint):
        """Bind an isolated request to its current issued authority."""
        return RepositoryKnowledge(self._root, checkpoint)

    def __init__(self, root: Path, authorize):
        if (not isinstance(root, Path) or not root.is_absolute()
                or root.resolve(strict=False) != root or not callable(authorize)):
            raise KnowledgeError("INVALID_KNOWLEDGE_CONFIGURATION")
        self._root = root
        self._authorize = authorize

    def _snapshot(self):
        registry = _registry()
        sources = []
        for source in registry["sources"]:
            value = copy.deepcopy(source)
            value["verification_status"] = "UNAVAILABLE"
            try:
                raw = _read(self._root, source["path"])
                observed = hashlib.sha256(raw).hexdigest()
                value["observed_sha256"] = observed
                if observed != source["sha256"]:
                    value["verification_status"] = "CHANGED"
                elif source["kind"] == "python_definition" and not set(source["symbols"]) <= _symbols(raw):
                    value["verification_status"] = "DEFINITION_MISSING"
                elif any(marker.encode() not in raw for marker in source.get("required_markers", [])):
                    value["verification_status"] = "CONTRADICTORY"
                else:
                    value["verification_status"] = "VERIFIED_EXACT_SOURCE"
            except (KnowledgeError, SyntaxError, UnicodeError, ValueError):
                pass
            # Do not return source text or internal marker definitions.
            value.pop("required_markers", None)
            sources.append(value)
        by_id = {s["source_id"]: s for s in sources}
        capabilities = []
        for record in registry["capabilities"]:
            value = copy.deepcopy(record)
            value["verification_status"] = "REPOSITORY_BOUND"
            value["evidence_references"] = [copy.deepcopy(by_id[s]) for s in record["evidence_references"]]
            if any(s["verification_status"] != "VERIFIED_EXACT_SOURCE" for s in value["evidence_references"]):
                value["implementation_status"] = "UNKNOWN"
                value["verification_status"] = "UNVERIFIED"
                value["description"] = "Repository evidence is unavailable or has changed; this capability cannot currently be verified."
                value["limitations"].append("Restore reviewed repository evidence before relying on implementation claims.")
            capabilities.append(value)
        return {"schema_version": registry["schema_version"], "registry_version": registry["registry_version"],
                "capabilities": capabilities, "source_records": sources,
                "governance": copy.deepcopy(registry["governance"]),
                "limitations": list(registry["limitations"])}

    def snapshot(self):
        self._authorize()
        result = self._snapshot()
        self._authorize()
        return result

    def retrieve(self, question, max_items=8):
        self._authorize()
        if (type(question) is not str or not 1 <= len(question) <= 8000
                or type(max_items) is not int or not 1 <= max_items <= 16):
            raise KnowledgeError("INVALID_KNOWLEDGE_QUERY")
        tokens = set(re.findall(r"[a-z0-9]+", question.lower()))
        all_capabilities = bool(tokens & {"capabilities", "architecture", "built", "subsystems"}) or {"what", "do"} <= tokens
        requested_statuses = {status for status in _STATUSES if status.lower() in tokens}
        snapshot = self._snapshot()
        scored = []
        for index, capability in enumerate(snapshot["capabilities"]):
            score = len(tokens & set(capability["keywords"]))
            if requested_statuses:
                if capability["implementation_status"] not in requested_statuses:
                    continue
                score += 1
            if score or all_capabilities:
                scored.append((score, -index, capability))
        scored.sort(key=lambda row: row[:2], reverse=True)
        results = []
        for _, _, capability in scored[:max_items]:
            citations = [{key: source[key] for key in
                          ("source_id", "path", "sha256", "kind", "version", "symbols")}
                         for source in capability["evidence_references"]
                         if source["verification_status"] == "VERIFIED_EXACT_SOURCE"]
            results.append({"capability_id": capability["capability_id"],
                            "text": capability["description"],
                            "implementation_status": capability["implementation_status"],
                            "authorization_status": capability["authorization_status"],
                            "verification_status": capability["verification_status"],
                            "citations": citations,
                            "limitations": list(capability["limitations"])})
        self._authorize()
        return results
