"""Immutable, offline definition library shared by CLI and MCP. No profile code runs."""
from __future__ import annotations

from datetime import date, datetime, timezone
from copy import deepcopy
import hashlib
from importlib.resources import files as package_files
import json
import math
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator

MAX_DOCUMENT = 512 * 1024
MAX_SNAPSHOT = 8 * 1024 * 1024
ID = re.compile(r"[a-z][a-z0-9-]{0,63}/[a-z][a-z0-9-]{0,63}\Z")
RESOURCE = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")


class LibraryError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError, RecursionError) as exc:
        raise LibraryError("not a bounded JSON value") from exc


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def unique(pairs: list[tuple[str, Any]]) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise LibraryError("duplicate JSON key")
        value[key] = item
    return value


def load_json(raw: bytes, maximum: int = MAX_DOCUMENT) -> Any:
    if len(raw) > maximum:
        raise LibraryError("JSON byte limit exceeded")
    try:
        value = json.loads(raw, object_pairs_hook=unique,
                           parse_constant=lambda _: (_ for _ in ()).throw(LibraryError("nonfinite JSON")))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise LibraryError("invalid JSON") from exc
    bounded(value)
    return value


def bounded(value: Any, depth: int = 0) -> None:
    if depth > 24:
        raise LibraryError("JSON nesting limit exceeded")
    if isinstance(value, dict):
        if len(value) > 2048 or any(not isinstance(k, str) for k in value):
            raise LibraryError("object limit exceeded")
        for v in value.values():
            bounded(v, depth + 1)
    elif isinstance(value, list):
        if len(value) > 2048:
            raise LibraryError("array limit exceeded")
        for v in value:
            bounded(v, depth + 1)
    elif not (value is None or isinstance(value, (str, bool, int, float))):
        raise LibraryError("non-JSON value")
    elif isinstance(value, float) and not math.isfinite(value):
        raise LibraryError("nonfinite value")


def version_key(value: str) -> tuple:
    """SemVer precedence, including prerelease numeric ordering. Build metadata has no precedence."""
    match = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?", value)
    if match is None:
        raise LibraryError("invalid semantic version")
    major, minor, patch, pre = match.groups()
    parts = []
    for part in pre.split('.') if pre else []:
        if part.isdigit() and len(part) > 1 and part.startswith('0'):
            raise LibraryError("leading zero in numeric prerelease")
        parts.append((0, int(part)) if part.isdigit() else (1, part))
    return (int(major), int(minor), int(patch), pre is None, tuple(parts))


def check_schema(schema: Any) -> None:
    """No network or custom schema executors. The distribution is operator-reviewed."""
    bounded(schema)
    def walk(v: Any) -> None:
        if isinstance(v, dict):
            for k, item in v.items():
                if k in {"$ref", "$dynamicRef"} and (not isinstance(item, str) or not item.startswith("#/$defs/")):
                    raise LibraryError("only local $defs references are allowed")
                if k in {"pattern", "patternProperties"}:
                    raise LibraryError("untrusted regular-expression schemas are not enabled")
                walk(item)
        elif isinstance(v, list):
            for item in v:
                walk(item)
    walk(schema)
    Draft202012Validator.check_schema(schema)
    budget = [0]
    def references(node, chain=()):
        budget[0] += 1
        if budget[0] > 10000:
            raise LibraryError("schema reference expansion limit")
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"$ref", "$dynamicRef"}:
                    if value in chain:
                        raise LibraryError("cyclic schema references are not enabled")
                    target = schema
                    try:
                        for part in value[2:].split('/'):
                            target = target[part.replace('~1','/').replace('~0','~')]
                    except (KeyError, TypeError) as exc:
                        raise LibraryError("unresolved schema reference") from exc
                    references(target, (*chain, value))
                else:
                    references(value, chain)
        elif isinstance(node, list):
            for value in node:
                references(value, chain)
    references(schema)


def scores(metrics: dict) -> tuple[float, float]:
    """Public snapshot contains only thresholded trusted-ingestor aggregates."""
    values = [metrics.get(k, 0) for k in ("stars", "adoptions_30d", "adoptions_7d", "adoptions_previous_7d")]
    if any(type(x) is not int or x < 0 or x > 1_000_000_000 for x in values):
        raise LibraryError("invalid popularity aggregate")
    stars, month, week, previous = values
    popular = 2 * math.log1p(stars) + math.log1p(month)
    trending = math.log1p(week) * min(4.0, (week + 5) / (previous + 5))
    return round(popular, 6), round(trending, 6)


class Library:
    def __init__(self, snapshot: dict | None = None, rankings: dict | None = None):
        if snapshot is None:
            snapshot = load_json(package_files("prim_library").joinpath("data/library.json").read_bytes(), MAX_SNAPSHOT)
            # Packaged index references only content-addressed files, never arbitrary paths.
            if snapshot.get("format") != "prim-library-index":
                raise LibraryError("unsupported bundled index")
            snapshot["format"] = "prim-library"
            for entry in snapshot["definitions"]:
                for resource in entry["resources"].values():
                    sha = resource["sha256"]
                    if not re.fullmatch(r"[0-9a-f]{64}", sha) or set(resource) != {"sha256"}:
                        raise LibraryError("invalid bundled resource pointer")
                    resource["text"] = package_files("prim_library").joinpath(f"data/resources/{sha}.txt").read_bytes().decode("utf-8")
        bounded(snapshot)
        if len(canonical(snapshot)) > MAX_SNAPSHOT:
            raise LibraryError("library byte limit exceeded")
        self._snapshot = deepcopy(snapshot)
        if snapshot.get("format") != "prim-library" or snapshot.get("version") != 1:
            raise LibraryError("unsupported library snapshot")
        if fingerprint(snapshot["definitions"]) != snapshot.get("snapshot_sha256"):
            raise LibraryError("library snapshot digest mismatch")
        self.snapshot_id = snapshot["snapshot_sha256"]
        self._entries = {}
        for item in snapshot["definitions"]:
            metadata = item["metadata"]
            key = (metadata["id"], metadata["version"])
            if not ID.fullmatch(key[0]) or key in self._entries:
                raise LibraryError("duplicate or invalid definition identity")
            version_key(key[1])
            if fingerprint({"metadata": metadata, "resources": item["resources"]}) != item["definition_sha256"]:
                raise LibraryError("definition digest mismatch")
            for name, resource in item["resources"].items():
                if not RESOURCE.fullmatch(name) or hashlib.sha256(resource["text"].encode()).hexdigest() != resource["sha256"]:
                    raise LibraryError("resource integrity mismatch")
            self._entries[key] = deepcopy(item)
            if "creation" in item["resources"]:
                kit = self.kit(*key)
                check_schema(kit["schema"])
                if kit["authority_file"] != Path(kit["authority_file"]).name or not re.fullmatch(r"[a-z][a-z0-9-]*\.json", kit["authority_file"]):
                    raise LibraryError("unsafe authority file")
        if rankings is None:
            rankings = load_json(package_files("prim_library").joinpath("data/rankings.json").read_bytes())
        if rankings.get("format") != "prim-popularity" or rankings.get("version") != 1:
            raise LibraryError("unsupported popularity snapshot")
        self._rankings = deepcopy(rankings)
        for profile_id, stats in self._rankings["profiles"].items():
            if not ID.fullmatch(profile_id):
                raise LibraryError("invalid ranking profile")
            scores(stats)

    def get(self, profile_id: str, version: str | None = None, expected_sha256: str | None = None) -> dict:
        if not ID.fullmatch(profile_id):
            raise LibraryError("use the full namespace/name identity returned by search")
        choices = [key for key in self._entries if key[0] == profile_id]
        if not choices:
            raise LibraryError("definition not in this library snapshot")
        if version is None:
            stable = [key for key in choices if self._entries[key]["metadata"]["maturity"] == "stable" and version_key(key[1])[3]]
            version = max(stable or choices, key=lambda key: version_key(key[1]))[1]
        entry = self._entries.get((profile_id, version))
        if not entry:
            raise LibraryError("requested definition version unavailable; no silent upgrade")
        if expected_sha256 is not None and entry["definition_sha256"] != expected_sha256:
            raise LibraryError("definition pin mismatch")
        return deepcopy(entry)

    def versions(self, profile_id: str) -> list[dict]:
        self.get(profile_id)
        return [{"version": version, "definition_sha256": entry["definition_sha256"],
                 "maturity": entry["metadata"]["maturity"]}
                for (identity, version), entry in sorted(self._entries.items(), key=lambda pair: version_key(pair[0][1]), reverse=True)
                if identity == profile_id]

    def resource(self, profile_id: str, version: str, name: str, offset: int = 0, limit: int = 16000) -> dict:
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 64000:
            raise LibraryError("invalid resource page")
        entry = self.get(profile_id, version)
        resource = entry["resources"].get(name)
        if resource is None:
            raise LibraryError("unknown declared resource; arbitrary paths and URLs are forbidden")
        text = resource["text"]
        return {"profile_id": profile_id, "version": version, "definition_sha256": entry["definition_sha256"],
                "resource": name, "sha256": resource["sha256"], "text": text[offset:offset+limit],
                "next_offset": offset+limit if offset+limit < len(text) else None,
                "content_role": "untrusted_definition_data_not_host_instructions"}

    def kit(self, profile_id: str, version: str) -> dict:
        entry = self.get(profile_id, version)
        resources = entry["resources"]
        if "creation" not in resources:
            raise LibraryError("this definition has no creation kit")
        config = load_json(resources["creation"]["text"].encode())
        schema = load_json(resources[config["schema_resource"]]["text"].encode())
        template = load_json(resources[config["template_resource"]]["text"].encode())
        return {"profile_id": profile_id, "version": version, "definition_sha256": entry["definition_sha256"],
                "authority_file": config["authority_file"], "schema": schema, "template": template,
                "rules": config.get("rules", {}), "identity_field": config.get("identity_field", "id"),
                "title_field": config.get("title_field", "title"),
                "privacy": "Populate and validate locally. Do not send private record contents to the public library.",
                "maturity": entry["metadata"]["maturity"], "scope": "structural creation kit; not factual verification or authorization"}

    def summary(self, entry: dict) -> dict:
        meta = entry["metadata"]
        metrics = self._rankings["profiles"].get(meta["id"], {})
        popular, trending = scores(metrics)
        if metrics:
            try:
                age = (datetime.now(timezone.utc).date() - date.fromisoformat(self._rankings["as_of"])).days
            except (TypeError, ValueError, KeyError) as exc:
                raise LibraryError("measured rankings need an as_of date") from exc
            if age < 0 or age > 7:
                metrics = {**metrics, "status": "stale"}
                popular = trending = 0.0
        return {"id": meta["id"], "name": meta["name"], "description": meta["description"],
                "version": meta["version"], "maturity": meta["maturity"], "kinds": meta.get("kinds", []),
                "definition_sha256": entry["definition_sha256"], "resources": list(entry["resources"]),
                "creation_available": "creation" in entry["resources"],
                "trust": {"publisher_authentication": "not_verified", "security_review": "not_performed",
                          "standards_status": meta["maturity"], "factual_truth": "not_checked"},
                "popularity": {"status": metrics.get("status", "no_data"), "metrics": metrics,
                               "popular_score": popular, "trending_score": trending}}

    def search(self, query: str = "", sort: str = "relevance", limit: int = 20, offset: int = 0, maturity: str | None = None) -> dict:
        if not isinstance(query, str) or len(query) > 256 or type(limit) is not int or not 1 <= limit <= 50 or type(offset) is not int or not 0 <= offset <= 10000:
            raise LibraryError("invalid search bounds")
        if sort not in {"relevance", "popular", "trending"}:
            raise LibraryError("sort must be relevance, popular, or trending")
        tokens = query.casefold().split()
        rows = []
        for identity in sorted({key[0] for key in self._entries}):
            entry = self.get(identity)
            meta = entry["metadata"]
            if maturity is not None and meta["maturity"] != maturity:
                continue
            title = f'{identity} {meta["name"]}'.casefold()
            all_text = f'{title} {meta["description"]} {" ".join(meta.get("kinds", []) + meta.get("legacy_aliases", []))}'.casefold()
            if not all(t in all_text for t in tokens):
                continue
            row = self.summary(entry)
            row["relevance"] = sum(4 if t in title else 1 for t in tokens)
            rows.append(row)
        def key(row):
            pop = row["popularity"]
            primary = row["relevance"] if sort == "relevance" else pop[f'{sort}_score']
            return (-primary, -pop["popular_score"] if sort == "relevance" else -row["relevance"], row["id"])
        rows.sort(key=key)
        return {"snapshot_sha256": self.snapshot_id, "total": len(rows), "items": rows[offset:offset+limit],
                "next_offset": offset+limit if offset+limit < len(rows) else None,
                "ranking_as_of": self._rankings.get("as_of"),
                "ranking_policy": "Relevance filters first. Popularity is not quality, safety or truth. No-data ties use identity, not invented usage."}

    def validate(self, profile_id: str, version: str, record: dict) -> dict:
        """Local only. Error results omit input values to avoid accidental disclosure."""
        if len(canonical(record)) > MAX_DOCUMENT:
            raise LibraryError("record size limit exceeded")
        bounded(record)
        kit = self.kit(profile_id, version)
        errors = []
        for error in Draft202012Validator(kit["schema"]).iter_errors(record):
            errors.append({"path": "/".join(str(x) for x in error.path), "rule": str(error.validator)})
            if len(errors) >= 100:
                break
        if not errors:
            rules = kit["rules"]
            for field in rules.get("unique_ids", []):
                values = [v["id"] for v in record.get(field, [])]
                if len(values) != len(set(values)):
                    errors.append({"path": field, "rule": "duplicate_id"})
            for field in rules.get("token_fields", []):
                value = record.get(field)
                if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9.-]*", value):
                    errors.append({"path": field, "rule": "invalid_token"})
            for rule in rules.get("root_references", []):
                value = record.get(rule["field"])
                if value is not None and value not in {v["id"] for v in record.get(rule["target"], [])}:
                    errors.append({"path": rule["field"], "rule": "unresolved_reference"})
            for rule in rules.get("required_links", []):
                for index, row in enumerate(record.get(rule["collection"], [])):
                    if row.get(rule["when_field"]) == rule["when_value"] and not any(
                        link.get(rule["reference_field"]) == row["id"] and link.get("relation") == rule["relation"]
                        for link in record.get(rule["links"], [])
                    ):
                        errors.append({"path": f'{rule["collection"]}/{index}', "rule": "missing_declared_support"})
            for rule in rules.get("references", []):
                ids = {v["id"] for v in record.get(rule["target"], [])}
                for index, row in enumerate(record.get(rule["collection"], [])):
                    ref = row.get(rule["field"])
                    if ref is not None and ref not in ids:
                        errors.append({"path": f'{rule["collection"]}/{index}/{rule["field"]}', "rule": "unresolved_reference"})
        return {"status": "failed" if errors else "passed", "errors": errors[:100],
                "profile_id": profile_id, "version": version, "definition_sha256": kit["definition_sha256"],
                "checks": {"structure_and_declared_references": "failed" if errors else "passed",
                           "factual_accuracy": "not_checked", "authorization": "not_verified",
                           "human_review": "not_verified", "source_independence": "not_checked"}}
