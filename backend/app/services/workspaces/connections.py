"""Build, validate, and communicate deterministic Canon connections.

Paths establish identities. Exact links resolve first; ambiguous abbreviated
references stay unresolved rather than acquiring invented provenance.
"""
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re

from app.core.canon.classifier import classify_document
from app.core.canon.discovery import CANON_ROOT
from app.core.canon.extractor import extract_document_signals
from app.services.workspaces.models import ConnectionEdge, ConnectionNode, ConnectionSnapshot


class ConnectionBuilder:
    def __init__(self, root: Path = CANON_ROOT):
        self.root = root.resolve()

    def build(self) -> ConnectionSnapshot:
        paths = sorted(self.root.rglob("*.md"))
        nodes, edges, unresolved = [], [], []
        by_path, aliases = {}, defaultdict(set)
        signals_by_id = {}
        for path in paths:
            relative = path.relative_to(self.root).as_posix()
            node_id = "document:" + relative
            metadata = classify_document(path)
            signals = extract_document_signals(path)
            nodes.append(ConnectionNode(id=node_id, title=signals["title"], path=relative,
                                        layer=metadata["layer"], type=metadata["type"]))
            by_path[path.resolve()] = node_id
            signals_by_id[node_id] = signals
            aliases[path.stem].add(node_id)
            match = re.match(r"^(ADR-\d{3}|Sprint-\d+(?:\.\d+)?)(?:-|$)", path.stem)
            if match:
                aliases[match.group(1)].add(node_id)
        for field, prefix in [("layer", "layer"), ("type", "type")]:
            for value in sorted({getattr(node, field) for node in nodes}):
                nodes.append(ConnectionNode(id=f"{prefix}:{value}", title=value.replace("_", " ").title(),
                                            layer="system", type=prefix))
        for node in nodes:
            if node.path is None:
                continue
            edges.extend([
                ConnectionEdge(source=node.id, target=f"layer:{node.layer}", relationship="belongs_to", basis="document classification"),
                ConnectionEdge(source=node.id, target=f"type:{node.type}", relationship="classified_as", basis="document classification"),
            ])
            signals = signals_by_id[node.id]
            for link in signals["links"]:
                target = urlsplit(link["target"])
                if target.scheme or target.netloc or not target.path.endswith(".md"):
                    continue
                resolved = (self.root / node.path).parent / unquote(target.path)
                target_id = by_path.get(resolved.resolve())
                if target_id and target_id != node.id:
                    edges.append(ConnectionEdge(source=node.id, target=target_id, relationship="references", basis="explicit Markdown link"))
                elif target_id is None:
                    unresolved.append({"source": node.id, "reference": link["target"], "reason": "missing_document"})
            for reference in signals["adr_mentions"] + signals["sprint_mentions"]:
                candidates = aliases.get(reference, set())
                if node.id in candidates:
                    continue
                if len(candidates) == 1:
                    edges.append(ConnectionEdge(source=node.id, target=next(iter(candidates)), relationship="references", basis="unique document reference"))
                else:
                    unresolved.append({"source": node.id, "reference": reference,
                                       "reason": "ambiguous_reference" if candidates else "missing_document"})
        edges = sorted({(e.source, e.target, e.relationship, e.basis): e for e in edges}.values(),
                       key=lambda e: (e.source, e.target, e.relationship, e.basis))
        return ConnectionSnapshot(nodes=nodes, edges=edges, unresolved_references=unresolved,
                                  relationships=dict(Counter(e.relationship for e in edges)))


class ConnectionValidator:
    def validate(self, snapshot: ConnectionSnapshot) -> None:
        identities = {node.id for node in snapshot.nodes}
        if len(identities) != len(snapshot.nodes):
            raise ValueError("Connection identities must be unique.")
        if any(edge.source not in identities or edge.target not in identities for edge in snapshot.edges):
            raise ValueError("Connections require existing source and target documents.")


class ConnectionRenderer:
    def render(self, snapshot: ConnectionSnapshot) -> dict:
        return snapshot.model_dump()


class ConnectionEngine:
    def __init__(self, root: Path = CANON_ROOT):
        self.builder = ConnectionBuilder(root)
        self.validator = ConnectionValidator()
        self.renderer = ConnectionRenderer()

    def inspect(self) -> dict:
        snapshot = self.builder.build()
        self.validator.validate(snapshot)
        return self.renderer.render(snapshot)
