"""Validate the canonical Open Product Format v1 graph."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from . import OPF_VERSION

ENTITY_TYPES = {
    "product", "area", "intent", "user", "problem", "promise", "outcome",
    "journey", "moment", "surface", "state", "interaction", "decision",
    "work", "evidence", "proof", "authority", "gap",
}
STATUSES = {
    "proposed", "active", "blocked", "validated", "building", "operating",
    "complete", "retired", "rejected",
}
EVENT_TYPES = {"created", "updated", "accepted", "status-changed", "observed", "log"}
ID_RE = re.compile(r"^[a-z][a-z0-9.-]*(?::[a-z0-9][a-z0-9._-]*)+$")
RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
ANY = ENTITY_TYPES
NON_ROOT = ENTITY_TYPES - {"product", "area"}
RELATION_RULES: dict[str, tuple[set[str], set[str]]] = {
    "expresses": ({"product"}, {"intent"}),
    "for-user": ({"problem", "promise", "outcome", "journey"}, {"user"}),
    "addresses": ({"promise"}, {"problem"}),
    "serves": ({"promise", "journey", "moment", "surface", "interaction", "work"}, {"outcome"}),
    "has-step": ({"journey"}, {"moment"}),
    "uses": ({"moment"}, {"surface"}),
    "has-state": ({"surface"}, {"state"}),
    "allows": ({"state"}, {"interaction"}),
    "transitions-to": ({"interaction"}, {"state"}),
    "realizes": ({"interaction"}, {"outcome"}),
    "decides": ({"decision"}, NON_ROOT),
    "governed-by": (NON_ROOT, {"authority"}),
    "implements": ({"work"}, {"promise", "decision", "surface", "interaction", "outcome"}),
    "supported-by": (ANY - {"evidence"}, {"evidence"}),
    "verified-by": (ANY - {"proof"}, {"proof"}),
    "blocks": ({"gap"}, NON_ROOT),
    "depends-on": (NON_ROOT, NON_ROOT),
    "supersedes": (NON_ROOT, NON_ROOT),
}


@dataclass
class Problem:
    level: str
    rule: str
    detail: str


@dataclass
class Report:
    path: Path
    problems: list[Problem] = field(default_factory=list)

    @property
    def errors(self) -> list[Problem]:
        return [problem for problem in self.problems if problem.level == "error"]


def _problem(problems: list[Problem], rule: str, detail: str) -> None:
    problems.append(Problem("error", rule, detail))


def _timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not RFC3339_RE.fullmatch(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def load_model(root: Path) -> tuple[dict[str, Any], list[Problem]]:
    path = root / "product.json"
    if not path.is_file():
        return {}, [Problem("error", "model_missing", "pack requires product.json")]
    try:
        model = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {}, [Problem("error", "model_json", str(error))]
    if not isinstance(model, dict):
        return {}, [Problem("error", "model_shape", "product.json must contain an object")]
    return model, []


def validate_model(model: dict[str, Any], root: Path) -> list[Problem]:
    problems: list[Problem] = []
    if model.get("format") != "opf" or model.get("version") != OPF_VERSION:
        _problem(problems, "format_version", f"format/version must be opf/{OPF_VERSION}")

    raw_entities = model.get("entities")
    if not isinstance(raw_entities, list) or not raw_entities:
        _problem(problems, "entities", "entities must be a nonempty list")
        return problems

    entities: dict[str, dict[str, Any]] = {}
    for index, entity in enumerate(raw_entities):
        if not isinstance(entity, dict):
            _problem(problems, "entity_shape", f"entities[{index}] must be an object")
            continue
        entity_id = entity.get("id")
        if not isinstance(entity_id, str) or not ID_RE.fullmatch(entity_id):
            _problem(problems, "entity_id", f"entities[{index}] has invalid id")
            continue
        if entity_id in entities:
            _problem(problems, "duplicate_entity", entity_id)
            continue
        entities[entity_id] = entity
        if entity.get("type") not in ENTITY_TYPES:
            _problem(problems, "entity_type", f"{entity_id}: {entity.get('type')!r}")
        if not isinstance(entity.get("title"), str) or not entity["title"].strip():
            _problem(problems, "entity_title", f"{entity_id}: title is required")
        if entity.get("status") not in STATUSES:
            _problem(problems, "entity_status", f"{entity_id}: {entity.get('status')!r}")
        provenance = entity.get("provenance")
        if not isinstance(provenance, dict) or not provenance.get("by") or not provenance.get("method"):
            _problem(problems, "entity_provenance", f"{entity_id}: provenance.by/method required")
        content = entity.get("content")
        if content:
            target = (root / str(content)).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                _problem(problems, "content_path", f"{entity_id}: content escapes pack")
            else:
                if not target.is_file():
                    _problem(problems, "content_missing", f"{entity_id}: {content}")

    root_id = model.get("product")
    if root_id not in entities or entities.get(root_id, {}).get("type") != "product":
        _problem(problems, "product_root", "product must resolve to one product entity")
    if sum(entity.get("type") == "product" for entity in entities.values()) != 1:
        _problem(problems, "product_count", "exactly one product entity is required")

    raw_relationships = model.get("relationships")
    if not isinstance(raw_relationships, list):
        _problem(problems, "relationships", "relationships must be a list")
        raw_relationships = []
    relationship_ids: set[str] = set()
    parents: dict[str, list[str]] = {entity_id: [] for entity_id in entities}
    children: dict[str, list[str]] = {entity_id: [] for entity_id in entities}
    sibling_orders: set[tuple[str, int]] = set()
    for index, relationship in enumerate(raw_relationships):
        if not isinstance(relationship, dict):
            _problem(problems, "relationship_shape", f"relationships[{index}] must be an object")
            continue
        rel_id = relationship.get("id")
        if not isinstance(rel_id, str) or not ID_RE.fullmatch(rel_id) or rel_id in relationship_ids:
            _problem(problems, "relationship_id", f"relationships[{index}] invalid or duplicate id")
        else:
            relationship_ids.add(rel_id)
        source, target, rel_type = relationship.get("from"), relationship.get("to"), relationship.get("type")
        if source not in entities or target not in entities:
            _problem(problems, "relationship_endpoint", f"{rel_id}: {source} -> {target}")
            continue
        source_type, target_type = entities[source].get("type"), entities[target].get("type")
        if rel_type == "contains":
            allowed = (
                (source_type == "product" and target_type == "area")
                or (source_type == "area" and target_type in NON_ROOT)
                or (source_type == "journey" and target_type == "moment")
                or (source_type == "surface" and target_type == "state")
                or (source_type == "state" and target_type == "interaction")
            )
            if not allowed:
                _problem(problems, "contains_type", f"{rel_id}: {source_type} -> {target_type}")
            parents[target].append(source)
            children[source].append(target)
            order = relationship.get("order")
            if not isinstance(order, int) or order < 0:
                _problem(problems, "contains_order", f"{rel_id}: nonnegative integer order required")
            elif (source, order) in sibling_orders:
                _problem(problems, "contains_order", f"{rel_id}: duplicate sibling order {order}")
            else:
                sibling_orders.add((source, order))
        elif rel_type not in RELATION_RULES:
            _problem(problems, "relationship_type", f"{rel_id}: {rel_type!r}")
        else:
            sources, targets = RELATION_RULES[rel_type]
            if source_type not in sources or target_type not in targets:
                _problem(problems, "relationship_types", f"{rel_id}: {source_type} -{rel_type}-> {target_type}")
            if rel_type == "supersedes" and source_type != target_type:
                _problem(problems, "supersedes_type", f"{rel_id}: kinds differ")
            if rel_type == "has-step" and not isinstance(relationship.get("order"), int):
                _problem(problems, "step_order", f"{rel_id}: integer order required")

    for entity_id in entities:
        count = len(parents[entity_id])
        if entity_id == root_id and count:
            _problem(problems, "hierarchy_root", "product root cannot have a parent")
        elif entity_id != root_id and count != 1:
            _problem(problems, "hierarchy_parent", f"{entity_id}: expected one parent, found {count}")
    seen: set[str] = set()
    pending = [root_id] if root_id in entities else []
    while pending:
        current = pending.pop()
        if current in seen:
            _problem(problems, "hierarchy_cycle", current)
            continue
        seen.add(current)
        pending.extend(children[current])
    if set(entities) - seen:
        _problem(problems, "hierarchy_reachability", f"unreachable: {sorted(set(entities) - seen)}")

    raw_events = model.get("events")
    if not isinstance(raw_events, list):
        _problem(problems, "events", "events must be a list")
        raw_events = []
    event_ids: set[str] = set()
    created = {entity_id: 0 for entity_id in entities}
    for index, event in enumerate(raw_events):
        if not isinstance(event, dict):
            _problem(problems, "event_shape", f"events[{index}] must be an object")
            continue
        event_id, event_type = event.get("id"), event.get("type")
        if not isinstance(event_id, str) or not ID_RE.fullmatch(event_id) or event_id in event_ids:
            _problem(problems, "event_id", f"events[{index}] invalid or duplicate id")
        else:
            event_ids.add(event_id)
        if event_type not in EVENT_TYPES:
            _problem(problems, "event_type", f"{event_id}: {event_type!r}")
        if not _timestamp(event.get("at")):
            _problem(problems, "event_timestamp", f"{event_id}: RFC 3339 timestamp required")
        subjects = event.get("subjects")
        if not isinstance(subjects, list) or (event_type != "log" and not subjects):
            _problem(problems, "event_subjects", f"{event_id}: subjects required (log may be empty)")
            subjects = []
        unresolved = [subject for subject in subjects if subject not in entities]
        if unresolved:
            _problem(problems, "event_subject", f"{event_id}: {unresolved}")
        if not isinstance(event.get("detail"), str) or not event["detail"].strip():
            _problem(problems, "event_detail", f"{event_id}: detail required")
        if event_type == "created":
            for subject in subjects:
                created[subject] += 1
        if event_type == "accepted":
            if not event.get("actor") or any(entities.get(subject, {}).get("type") != "decision" for subject in subjects):
                _problem(problems, "accepted_event", f"{event_id}: decision subjects and actor required")
        for evidence_id in event.get("evidence", []):
            if entities.get(evidence_id, {}).get("type") not in {"evidence", "proof"}:
                _problem(problems, "event_evidence", f"{event_id}: {evidence_id}")
    for entity_id, count in created.items():
        if count != 1:
            _problem(problems, "created_event", f"{entity_id}: expected one created event, found {count}")
    return problems


def validate_pack(root: Path, *, strict: bool = False) -> list[Report]:
    del strict  # v1 has one fail-closed validation mode
    root = root.resolve()
    model, problems = load_model(root)
    if model:
        problems.extend(validate_model(model, root))
    return [Report(root / "product.json", problems)]


def selftest() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        model = {
            "format": "opf", "version": OPF_VERSION, "product": "opf:test:product",
            "entities": [
                {"id": "opf:test:product", "type": "product", "title": "Test", "status": "active", "provenance": {"by": "human:test", "method": "test"}},
                {"id": "opf:test:area", "type": "area", "title": "Intent", "status": "active", "provenance": {"by": "human:test", "method": "test"}},
            ],
            "relationships": [{"id": "opf:test:rel:1", "type": "contains", "from": "opf:test:product", "to": "opf:test:area", "order": 0}],
            "events": [
                {"id": "opf:test:event:1", "type": "created", "at": "2026-08-08T00:00:00Z", "subjects": ["opf:test:product"], "detail": "Created product"},
                {"id": "opf:test:event:2", "type": "created", "at": "2026-08-08T00:00:01Z", "subjects": ["opf:test:area"], "detail": "Created area"},
            ],
        }
        (root / "product.json").write_text(json.dumps(model))
        assert not validate_pack(root)[0].errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an OPF v1 canonical product graph")
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("--strict", action="store_true", help="accepted for CLI continuity; v1 is always strict")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        selftest()
        print("ok    selftest")
        return 0
    if args.path is None:
        parser.error("path is required unless --selftest is used")
    reports = validate_pack(args.path, strict=args.strict)
    for report in reports:
        if report.problems:
            for problem in report.problems:
                print(f"{problem.level:5} {report.path}: {problem.rule}: {problem.detail}")
        else:
            print(f"ok    {report.path}")
    return 1 if any(report.errors for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
