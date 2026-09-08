"""Local authoring tool: public definitions in, private Prim files out. No network."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

from .library import Library, LibraryError, canonical, load_json, MAX_SNAPSHOT


def create(library: Library, profile_id: str, version: str, target: Path, values: dict | None = None) -> dict:
    kit = library.kit(profile_id, version)
    record = kit["template"]
    values = {} if values is None else values
    if not isinstance(values, dict):
        raise LibraryError("record input must be an object")
    record.update(values)
    field = kit["identity_field"]
    if not record.get(field):
        record[field] = "prim-" + uuid.uuid4().hex
    result = library.validate(profile_id, version, record)
    if result["status"] != "passed":
        raise LibraryError("record failed structural checks: " + json.dumps(result["errors"]))
    target = Path(os.path.abspath(target))
    if target.exists() or any(p.is_symlink() for p in [target, *target.parents]) or not target.parent.is_dir():
        raise LibraryError("target must be a new directory under a trusted existing nonsymlink parent")
    temp = Path(tempfile.mkdtemp(prefix=".prim-create-", dir=target.parent))
    title = record.get(kit["title_field"], "Untitled Prim")
    pin = {"profile_id": profile_id, "version": version, "definition_sha256": kit["definition_sha256"]}
    try:
        (temp / kit["authority_file"]).write_bytes(canonical(record) + b"\n")
        (temp / "prim-definition.lock.json").write_bytes(canonical(pin) + b"\n")
        # JSON-quoted YAML strings prevent frontmatter injection from user text.
        face = f'---\nprofile: {json.dumps(profile_id)}\nprofile_version: {json.dumps(version)}\ntype: {json.dumps(library.get(profile_id, version)["metadata"]["kinds"][0])}\ntitle: {json.dumps(title)}\nauthority: {kit["authority_file"]}\n---\n\nThis Prim\u2019s authoritative data is in `{kit["authority_file"]}`.\n'
        (temp / "index.md").write_text(face, encoding="utf-8")
        (temp / "log.md").write_text(f"# Log\n\n- {datetime.now(timezone.utc).isoformat()} — Created locally from a pinned definition; no factual or human approval claim.\n")
        if target.exists() or target.is_symlink():
            raise LibraryError("target appeared during creation")
        temp.rename(target)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return {"path": str(target), "pin": pin, "validation": result}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--library", type=Path, help="Explicit local compiled library; no URL fetch")
    sub = ap.add_subparsers(dest="command", required=True)
    host = sub.add_parser("export-host", help="Emit public, data-only kits for an offline native or SDK host")
    host.add_argument("--source-commit", default="unrecorded", help="Optional source provenance; not publisher authentication")
    pack = sub.add_parser("check-pack", help="Check a local Prim folder using its exact definition lock")
    pack.add_argument("path", type=Path)
    search = sub.add_parser("search")
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--sort", default="relevance", choices=["relevance", "popular", "trending"])
    for name in ["definition", "kit", "create", "validate"]:
        p = sub.add_parser(name)
        p.add_argument("profile_id")
        p.add_argument("--version", required=True)
        if name == "create":
            p.add_argument("--output", type=Path, required=True)
            p.add_argument("--input", type=Path)
        if name == "validate":
            p.add_argument("input", type=Path)
    args = ap.parse_args(argv)
    try:
        library = Library(load_json(args.library.read_bytes(), MAX_SNAPSHOT)) if args.library else Library()
        if args.command == "export-host":
            from .host_catalog import export_host_catalog
            result = export_host_catalog(library, args.source_commit)
        elif args.command == "check-pack":
            from .pack import read_pack
            # Validation output never prints private record values.
            result = read_pack(library, args.path)["validation"]
        elif args.command == "search":
            result = library.search(args.query, args.sort)
        elif args.command == "definition":
            result = library.get(args.profile_id, args.version)
        elif args.command == "kit":
            result = library.kit(args.profile_id, args.version)
        elif args.command == "create":
            result = create(library, args.profile_id, args.version, args.output,
                            load_json(args.input.read_bytes()) if args.input else None)
        else:
            result = library.validate(args.profile_id, args.version, load_json(args.input.read_bytes()))
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 1 if result.get("status") == "failed" else 0
    except (LibraryError, OSError) as exc:
        print(f"Prim Library: {exc}", file=__import__('sys').stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
