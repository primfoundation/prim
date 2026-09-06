#!/usr/bin/env python3
"""Validate the Foundation ledger and generate ROADMAP.md (standard library only)."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"planned", "in_progress", "blocked", "in_review", "complete"}
STAGES = {"implementation", "tests", "review", "release", "deployment", "real_use"}


class PlanError(ValueError):
    pass


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise PlanError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def read_plan(root: Path) -> dict[str, Any]:
    text = (root / "program/plan.json").read_text(encoding="utf-8")
    if len(text.encode("utf-8")) > 1_000_000:
        raise PlanError("program ledger size limit exceeded")
    return json.loads(text, object_pairs_hook=_unique)


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise PlanError(f"{label} must be a non-empty trimmed string")
    if any(ord(c) < 32 for c in value):
        raise PlanError(f"{label} contains control characters")
    return value


def _records(plan: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    rows = plan.get(key)
    if not isinstance(rows, list) or not rows:
        raise PlanError(f"{key} must be a non-empty list")
    records: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise PlanError(f"{key} entries must be objects")
        identifier = _string(row.get("id"), f"{key}.id")
        if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*", identifier):
            raise PlanError(f"invalid {key} id: {identifier}")
        if identifier in records:
            raise PlanError(f"duplicate {key} id: {identifier}")
        records[identifier] = row
    return records


def _list(row: dict[str, Any], key: str, allowed: set[str], *, nonempty: bool = False) -> list[str]:
    value = row.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise PlanError(f"{row['id']}.{key} must be a string list")
    if (nonempty and not value) or len(set(value)) != len(value):
        raise PlanError(f"{row['id']}.{key} is empty or contains duplicates")
    unknown = set(value) - allowed
    if unknown:
        raise PlanError(f"{row['id']}.{key} references unknown values: {sorted(unknown)}")
    return value


def _evidence_path(root: Path, name: str) -> Path:
    pure = PurePosixPath(name)
    if pure.is_absolute() or any(p in {"", ".", ".."} for p in name.split("/")) or "\\" in name or ":" in name:
        raise PlanError("evidence path must be a canonical local relative path")
    current = root
    for part in pure.parts:
        current /= part
        if current.is_symlink():
            raise PlanError("symlink evidence paths are not allowed")
    if not current.is_file():
        raise PlanError(f"evidence file missing: {name}")
    return current


def validate_plan(plan: Any, root: Path) -> None:
    if not isinstance(plan, dict) or type(plan.get("format_version")) is not int or plan["format_version"] != 1:
        raise PlanError("unsupported program format_version")
    for key in ("program", "mission", "as_of"):
        _string(plan.get(key), key)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", plan["as_of"]):
        raise PlanError("as_of must be YYYY-MM-DD")
    try:
        date.fromisoformat(plan["as_of"])
    except ValueError as exc:
        raise PlanError("as_of is not a valid date") from exc
    execution = plan.get("execution")
    if not isinstance(execution, dict):
        raise PlanError("execution state is required")
    for key in ("state", "target_repository", "base_commit", "target_branch", "background_jobs"):
        _string(execution.get(key), f"execution.{key}")
    if not re.fullmatch(r"[0-9a-f]{40}", execution["base_commit"]):
        raise PlanError("base_commit must be a full observed SHA")
    streams = _records(plan, "workstreams")
    milestones = _records(plan, "milestones")
    evidence = _records(plan, "evidence")
    requirements = _records(plan, "requirements")
    for stream in streams.values():
        _string(stream.get("name"), "workstream name")
        if stream.get("delivery") not in {"foundation", "reference", "ecosystem"}:
            raise PlanError("unknown workstream delivery responsibility")
    for milestone in milestones.values():
        _string(milestone.get("name"), "milestone name")
        _string(milestone.get("gate"), "milestone gate")
    for row in evidence.values():
        if row.get("stage") not in STAGES:
            raise PlanError("unknown evidence stage")
        _string(row.get("summary"), "evidence summary")
        _evidence_path(root, _string(row.get("path"), "evidence path"))
    for row in requirements.values():
        for key in ("title", "acceptance", "owner"):
            _string(row.get(key), f"{row['id']}.{key}")
        if row.get("workstream") not in streams or row.get("milestone") not in milestones:
            raise PlanError(f"{row['id']} has unknown workstream or milestone")
        if row.get("status") not in STATUSES:
            raise PlanError(f"{row['id']} has unknown status")
        if not isinstance(row.get("note"), str):
            raise PlanError(f"{row['id']} needs a note string (empty is allowed)")
        if row["status"] == "blocked" and not row["note"].strip():
            raise PlanError(f"{row['id']} blocked without a reason")
        deps = _list(row, "depends_on", set(requirements))
        stages = _list(row, "required_evidence", STAGES, nonempty=True)
        refs = _list(row, "evidence", set(evidence))
        if row["status"] == "complete":
            missing = set(stages) - {evidence[item]["stage"] for item in refs}
            if missing:
                raise PlanError(f"{row['id']} complete without required evidence: {sorted(missing)}")
            if any(requirements[item]["status"] != "complete" for item in deps):
                raise PlanError(f"{row['id']} complete with unfinished dependencies")
    for key, records in (("workstream", streams), ("milestone", milestones)):
        orphaned = set(records) - {row[key] for row in requirements.values()}
        if orphaned:
            raise PlanError(f"uncovered {key}: {sorted(orphaned)}")
    active: set[str] = set()
    done: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in active:
            raise PlanError(f"dependency cycle at {identifier}")
        if identifier in done:
            return
        active.add(identifier)
        for dependency in requirements[identifier]["depends_on"]:
            visit(dependency)
        active.remove(identifier)
        done.add(identifier)

    for identifier in requirements:
        visit(identifier)
    for key in ("life_domains", "coverage_lenses"):
        values = plan.get(key)
        if not isinstance(values, list) or not values:
            raise PlanError(f"{key} must retain coverage dimensions")
        for item in values:
            _string(item, key)
        if len(set(values)) != len(values):
            raise PlanError(f"duplicate {key}")


def render(plan: dict[str, Any]) -> str:
    rows = plan["requirements"]
    counts = Counter(row["status"] for row in rows)
    lines = ["# Prim Foundation roadmap", "", "Generated from `program/plan.json`. Do not edit statuses here.", "",
             f"As of {plan['as_of']}. Execution: **{plan['execution']['state']}**.", "",
             plan["mission"], "", "## Current evidence, not a mission percentage", "",
             f"{len(plan['workstreams'])} workstreams; {len(rows)} tracked requirements. " +
             "; ".join(f"{state}: {counts.get(state, 0)}" for state in sorted(STATUSES)) + ".", "",
             "Counts are an inventory, not equal-weight progress. In review is not accepted, released, deployed, or verified in real use.", "",
             "## Milestone acceptance gates", ""]
    for item in plan["milestones"]:
        lines += [f"### {item['id']} — {item['name']}", "", item["gate"], ""]
    lines += ["## Full coverage and delivery obligations", ""]
    for stream in plan["workstreams"]:
        lines += [f"### {stream['id']} — {stream['name']}", "", f"Delivery responsibility: {stream['delivery']}.", ""]
        for row in rows:
            if row["workstream"] != stream["id"]:
                continue
            lines += [f"**{row['id']} — {row['title']}**", "",
                      f"State: `{row['status']}` · Milestone: {row['milestone']} · Owner: {row['owner']}.", "",
                      f"Acceptance: {row['acceptance']}", "",
                      f"Required evidence: {', '.join(row['required_evidence'])}. " +
                      f"Evidence retained: {', '.join(row['evidence']) or 'none'}. " +
                      f"Dependencies: {', '.join(row['depends_on']) or 'none'}.", ""]
            if row["note"]:
                lines += [row["note"], ""]
    lines += ["## Whole-life coverage is not a type catalog", "", "; ".join(plan["life_domains"]) + ".", "",
              "## Cross-cutting coverage lenses", "", "; ".join(plan["coverage_lenses"]) + ".", "",
              "New discoveries extend this ledger. Deferral remains visible. Scope removal requires a recorded decision.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "render"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="Check generated ROADMAP.md instead of writing it")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        plan = read_plan(root)
        validate_plan(plan, root)
        if args.command == "check":
            print(f"Program valid: {len(plan['workstreams'])} workstreams, {len(plan['requirements'])} requirements; evidence references resolve.")
        else:
            output = root / "ROADMAP.md"
            expected = render(plan)
            if args.check:
                if not output.is_file() or output.read_text(encoding="utf-8") != expected:
                    raise PlanError("ROADMAP.md drift: run python tools/program.py render")
            else:
                if output.is_symlink():
                    raise PlanError("ROADMAP.md must not be a symlink")
                output.write_text(expected, encoding="utf-8")
        return 0
    except (OSError, PlanError, ValueError, RecursionError, TypeError) as exc:
        print(f"program: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
