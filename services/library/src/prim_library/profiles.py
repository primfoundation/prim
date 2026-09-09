#!/usr/bin/env python3
"""Local, read-only profile discovery. No network, imports, or validator execution.

Prototype contract: program/PROFILE-PACKAGE.md. Requires Python >=3.11 and
PyYAML 6.0.3. Run against a trusted, non-mutating local filesystem snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
from typing import Any

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML is required: python -m pip install -r tools/requirements.txt")

MAX_BYTES = 65536
MAX_EVENTS = 2048
MAX_DEPTH = 16
MAX_ENTRIES = 10000
MANIFEST = "PROFILE.md"
IGNORED = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
SLUG = r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*"
IDENTITY = re.compile(rf"{SLUG}/{SLUG}\Z")
VERSION = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?\Z"
)
MATURITIES = {"development", "alpha", "beta", "stable", "deprecated"}
FIELDS = {"format", "manifest_version", "id", "name", "description", "version",
          "maturity", "license", "kinds", "resources", "legacy_aliases", "extensions"}


class ProfileError(ValueError):
    """Invalid or unsupported profile input; never evidence of safe execution."""


class UniqueSafeLoader(yaml.SafeLoader):
    pass


def _mapping(loader: UniqueSafeLoader, node: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str) or key == "<<":
            raise ProfileError("metadata mapping keys must be strings; merges are forbidden")
        if key in result:
            raise ProfileError(f"duplicate metadata key: {key}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _metadata(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ProfileError("PROFILE.md must start with --- YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ProfileError("frontmatter closing --- is missing") from exc
    header = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1:]).strip()
    if not body:
        raise ProfileError("PROFILE.md needs a human-readable body")
    try:
        depth = 0
        for count, event in enumerate(yaml.parse(header), 1):
            if count > MAX_EVENTS:
                raise ProfileError("metadata event limit exceeded")
            if getattr(event, "anchor", None) or isinstance(event, yaml.AliasEvent):
                raise ProfileError("YAML anchors and aliases are not supported")
            if isinstance(event, (yaml.MappingStartEvent, yaml.SequenceStartEvent)):
                depth += 1
                if depth > MAX_DEPTH:
                    raise ProfileError("metadata nesting limit exceeded")
            if isinstance(event, (yaml.MappingEndEvent, yaml.SequenceEndEvent)):
                depth -= 1
        value = yaml.load(header, Loader=UniqueSafeLoader)
    except yaml.YAMLError as exc:
        raise ProfileError(f"invalid safe YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ProfileError("metadata must be a mapping")
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ProfileError("metadata must contain only JSON-compatible values; quote dates") from exc
    return value, body


def _text(data: dict[str, Any], key: str, maximum: int = 1024) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ProfileError(f"{key} must be a non-empty, trimmed string")
    if len(value) > maximum or any(ord(char) < 32 for char in value):
        raise ProfileError(f"{key} exceeds its size limit or contains control characters")
    return value


def _local_path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ProfileError("resource path must be a non-empty, trimmed string")
    if "\\" in value or ":" in value or "\x00" in value or any(ord(c) < 32 for c in value):
        raise ProfileError(f"resource is not a local POSIX relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ProfileError(f"resource path is not canonical and contained: {value!r}")
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ProfileError(f"symlink resource is not allowed: {value!r}")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
        mode = resolved.stat().st_mode
    except (OSError, ValueError, RuntimeError) as exc:
        raise ProfileError(f"resource missing or outside package: {value!r}") from exc
    if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
        raise ProfileError(f"resource is not a regular file or directory: {value!r}")
    return resolved


def _read_manifest(path: Path) -> bytes:
    if path.is_symlink():
        raise ProfileError("symlink manifest is not allowed")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        with os.fdopen(os.open(path, flags), "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise ProfileError("manifest must be a regular file")
            if info.st_size > MAX_BYTES:
                raise ProfileError("manifest size limit exceeded")
            raw = stream.read(MAX_BYTES + 1)
    except OSError as exc:
        raise ProfileError(f"cannot read manifest: {path.name}") from exc
    if len(raw) > MAX_BYTES:
        raise ProfileError("manifest size limit exceeded")
    return raw


def inspect_profile(location: str | Path) -> dict[str, Any]:
    supplied = Path(location)
    if supplied.is_symlink():
        raise ProfileError("symlink profile root is not allowed")
    path = supplied if supplied.name == MANIFEST else supplied / MANIFEST
    if path.parent.is_symlink():
        raise ProfileError("symlink profile root is not allowed")
    try:
        root = path.parent.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ProfileError("profile directory is missing") from exc
    raw = _read_manifest(path)
    try:
        data, _ = _metadata(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ProfileError("manifest must be UTF-8") from exc
    unknown = sorted(set(data) - FIELDS)
    if unknown:
        raise ProfileError(f"unknown metadata fields: {', '.join(unknown)}; use extensions")
    if data.get("format") != "prim-profile" or data.get("manifest_version") != "0.1":
        raise ProfileError("unsupported format or manifest_version (expected prim-profile / '0.1')")
    identity = _text(data, "id", 129)
    if not IDENTITY.fullmatch(identity) or any(len(p) > 64 for p in identity.split("/")):
        raise ProfileError("id must be namespace/name using lowercase kebab-case")
    if not VERSION.fullmatch(_text(data, "version", 128)):
        raise ProfileError("version must be an explicit semantic version, not a range")
    _text(data, "name", 128)
    _text(data, "description", 1024)
    if _text(data, "maturity", 32) not in MATURITIES:
        raise ProfileError("unknown maturity")
    if "license" in data:
        _text(data, "license", 128)
    for key in ("kinds", "legacy_aliases"):
        items = data.get(key, [])
        if not isinstance(items, list) or any(not isinstance(v, str) or not re.fullmatch(SLUG, v) for v in items):
            raise ProfileError(f"{key} must be a list of lowercase kebab-case strings")
        if len(items) > 128 or len(set(items)) != len(items):
            raise ProfileError(f"{key} contains duplicates or too many entries")
    resources = data.get("resources", {})
    if not isinstance(resources, dict) or len(resources) > 64:
        raise ProfileError("resources must be a mapping with at most 64 entries")
    for key, value in resources.items():
        if not re.fullmatch(SLUG, key):
            raise ProfileError("resource names must be lowercase kebab-case")
        _local_path(root, value)
    if "extensions" in data and not isinstance(data["extensions"], dict):
        raise ProfileError("extensions must be a mapping")
    return {
        "metadata": data,
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "checks": {
            "manifest": "passed",
            "declared_resource_paths": "passed",
            "profile_conformance": "not_checked",
            "publisher_identity": "not_verified",
            "security_review": "not_performed",
        },
    }


def discover_profiles(location: str | Path, *, max_depth: int = 8,
                      max_entries: int = MAX_ENTRIES) -> dict[str, Any]:
    supplied = Path(location)
    if supplied.is_symlink():
        raise ProfileError("symlink discovery root is not allowed")
    if max_depth < 0 or max_entries < 1:
        raise ProfileError("discovery bounds must be nonnegative depth and positive entries")
    try:
        root = supplied.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ProfileError("discovery directory is missing") from exc
    if not root.is_dir():
        raise ProfileError("discovery root must be a directory")
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    visited = 0

    def walk(directory: Path, depth: int) -> None:
        nonlocal visited
        entries = []
        with os.scandir(directory) as iterator:
            for entry in iterator:
                visited += 1
                if visited > max_entries:
                    raise ProfileError("discovery entry limit exceeded; narrow the source root")
                entries.append(entry)
        manifest = directory / MANIFEST
        if any(entry.name == MANIFEST for entry in entries):
            item = inspect_profile(manifest)
            key = (item["metadata"]["id"], item["metadata"]["version"])
            if key in seen:
                raise ProfileError(f"duplicate profile id/version: {key[0]}@{key[1]}")
            seen.add(key)
            item["location"] = manifest.relative_to(root).as_posix()
            result.append(item)
            return  # A package is a boundary: examples are not catalog publications.
        for entry in sorted(entries, key=lambda value: value.name):
            if entry.name in IGNORED:
                continue
            if entry.is_symlink():
                raise ProfileError("symlink found in discovery source; select an explicit package root")
            if entry.is_dir(follow_symlinks=False):
                if depth >= max_depth:
                    raise ProfileError("discovery depth limit exceeded; narrow the source root")
                walk(Path(entry.path), depth + 1)

    try:
        walk(root, 0)
    except OSError as exc:
        raise ProfileError("discovery could not read part of the source; no partial catalog emitted") from exc
    if not result:
        raise ProfileError("no PROFILE.md packages found; legacy folders are not automatically migrated")
    result.sort(key=lambda item: (item["metadata"]["id"], item["metadata"]["version"], item["location"]))
    return {"format": "prim-profile-catalog", "catalog_version": 1, "profiles": result}


def encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("inspect", "discover"))
    parser.add_argument("path")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--output", type=Path, help="Write an explicitly selected generated JSON view")
    target.add_argument("--check", type=Path, help="Fail if the generated JSON view has drifted")
    args = parser.parse_args(argv)
    try:
        operation = inspect_profile if args.command == "inspect" else discover_profiles
        rendered = encode(operation(args.path))
        if args.check:
            if not args.check.is_file() or args.check.read_text(encoding="utf-8") != rendered:
                raise ProfileError("generated catalog drift: regenerate the selected output")
        elif args.output:
            if args.output.suffix != ".json" or args.output.is_symlink():
                raise ProfileError("output must be an explicitly selected non-symlink .json file")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile("w", dir=args.output.parent, encoding="utf-8", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(rendered)
            try:
                os.replace(temporary, args.output)
            finally:
                temporary.unlink(missing_ok=True)
        else:
            sys.stdout.write(rendered)
        return 0
    except (ProfileError, OSError, ValueError) as exc:
        print(f"profile-catalog: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
