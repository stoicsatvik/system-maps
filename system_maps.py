from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

NODE_TYPES = frozenset({"actor", "resource"})
EDGE_TYPES = frozenset({"flow", "dependency", "feedback"})

@dataclass(frozen=True)
class Node:
    id: str
    type: str
    label: str

@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    type: str

@dataclass(frozen=True)
class SystemMap:
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def from_dict(payload: object) -> SystemMap:
    if not isinstance(payload, dict):
        raise ValueError("map must be an object")
    raw_nodes, raw_edges = payload.get("nodes"), payload.get("edges")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError("nodes must be a non-empty list")
    if not isinstance(raw_edges, list):
        raise ValueError("edges must be a list")
    nodes: list[Node] = []
    seen: set[str] = set()
    for item in raw_nodes:
        if not isinstance(item, dict):
            raise ValueError("node must be an object")
        node_id = _require_string(item.get("id"), "node.id")
        node_type = _require_string(item.get("type"), "node.type")
        label = _require_string(item.get("label", node_id), "node.label")
        if node_type not in NODE_TYPES:
            raise ValueError(f"unsupported node type: {node_type}")
        if node_id in seen:
            raise ValueError(f"duplicate node id: {node_id}")
        seen.add(node_id)
        nodes.append(Node(node_id, node_type, label))
    edges: list[Edge] = []
    for item in raw_edges:
        if not isinstance(item, dict):
            raise ValueError("edge must be an object")
        source = _require_string(item.get("source"), "edge.source")
        target = _require_string(item.get("target"), "edge.target")
        edge_type = _require_string(item.get("type"), "edge.type")
        if edge_type not in EDGE_TYPES:
            raise ValueError(f"unsupported edge type: {edge_type}")
        if source not in seen or target not in seen:
            raise ValueError("edge endpoints must reference existing nodes")
        edges.append(Edge(source, target, edge_type))
    return SystemMap(tuple(sorted(nodes, key=lambda n: n.id)), tuple(sorted(edges, key=lambda e: (e.source, e.target, e.type))))


def from_json(text: str) -> SystemMap:
    return from_dict(json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid JSON constant: {value}"))))


def to_json(system: SystemMap) -> str:
    payload = {
        "nodes": [{"id": n.id, "label": n.label, "type": n.type} for n in sorted(system.nodes, key=lambda n: n.id)],
        "edges": [{"source": e.source, "target": e.target, "type": e.type} for e in sorted(system.edges, key=lambda e: (e.source, e.target, e.type))],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def adjacency(system: SystemMap, edge_types: Iterable[str] | None = None) -> dict[str, tuple[str, ...]]:
    allowed = set(edge_types) if edge_types is not None else set(EDGE_TYPES)
    graph = {node.id: [] for node in system.nodes}
    for edge in system.edges:
        if edge.type in allowed:
            graph[edge.source].append(edge.target)
    return {key: tuple(sorted(values)) for key, values in graph.items()}


def cycles(system: SystemMap) -> tuple[tuple[str, ...], ...]:
    graph = adjacency(system)
    found: set[tuple[str, ...]] = set()
    def canonical(path: list[str]) -> tuple[str, ...]:
        ring = path[:-1]
        rotations = [tuple(ring[i:] + ring[:i]) for i in range(len(ring))]
        return min(rotations)
    def visit(start: str, current: str, path: list[str], used: set[str]) -> None:
        for nxt in graph[current]:
            if nxt == start:
                found.add(canonical(path + [start]))
            elif nxt not in used and nxt >= start:
                visit(start, nxt, path + [nxt], used | {nxt})
    for node in sorted(graph):
        visit(node, node, [node], {node})
    return tuple(sorted(found))


def dependency_counts(system: SystemMap) -> tuple[tuple[str, int], ...]:
    counts = {node.id: 0 for node in system.nodes}
    for edge in system.edges:
        if edge.type == "dependency":
            counts[edge.target] += 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def dependency_concentrations(system: SystemMap, minimum_dependents: int = 2) -> tuple[str, ...]:
    if minimum_dependents < 1:
        raise ValueError("minimum_dependents must be at least 1")
    return tuple(sorted(node for node, count in dependency_counts(system) if count >= minimum_dependents))


def _dependency_reachable(graph: dict[str, tuple[str, ...]], source: str, target: str, removed: str | None = None) -> bool:
    if source == removed or target == removed:
        return False
    pending = [source]
    seen = {source}
    while pending:
        current = pending.pop()
        for nxt in graph[current]:
            if nxt == removed:
                continue
            if nxt == target:
                return True
            if nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    return False


def single_points_of_failure(system: SystemMap) -> tuple[str, ...]:
    """Return dependency nodes whose removal disconnects a previously reachable pair.

    This is deliberately removal-based rather than an in-degree proxy. A heavily used
    dependency with an alternate dependency path is a concentration, not necessarily
    a structural single point of failure.
    """
    graph = adjacency(system, {"dependency"})
    nodes = tuple(sorted(graph))
    baseline = {
        (source, target)
        for source in nodes
        for target in nodes
        if source != target and _dependency_reachable(graph, source, target)
    }
    spofs: list[str] = []
    for candidate in nodes:
        disrupted = any(
            source != candidate
            and target != candidate
            and not _dependency_reachable(graph, source, target, removed=candidate)
            for source, target in baseline
        )
        if disrupted:
            spofs.append(candidate)
    return tuple(spofs)


def summary(system: SystemMap) -> str:
    ranked = dependency_counts(system)
    top = ranked[0] if ranked else ("none", 0)
    cycle_count = len(cycles(system))
    spofs = single_points_of_failure(system)
    concentrations = dependency_concentrations(system)
    return (f"{len(system.nodes)} nodes, {len(system.edges)} edges; "
            f"top dependency target={top[0]} ({top[1]} incoming); "
            f"cycles={cycle_count}; dependency_concentrations={','.join(concentrations) if concentrations else 'none'}; "
            f"single_points_of_failure={','.join(spofs) if spofs else 'none'}")
