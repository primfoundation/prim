"""Explicit local definition publishing. Data only; no network or profile execution."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import tempfile

from .library import Library, LibraryError, MAX_DOCUMENT, MAX_SNAPSHOT, canonical, fingerprint
from .profiles import ProfileError, discover_profiles, _local_path

EMPTY_RANKINGS = {"format": "prim-popularity", "version": 1, "profiles": {}}


def local_path(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise LibraryError("local paths must not contain symlinks")
    return path


def read_local(path: Path, maximum: int = MAX_SNAPSHOT) -> bytes:
    path = local_path(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
            raise LibraryError("input must be a bounded regular file")
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise LibraryError("input size limit exceeded")
    return raw


def write_new(path: Path, raw: bytes) -> None:
    """Publish a complete file atomically without replacing an existing destination."""
    path = local_path(path)
    if not path.parent.is_dir():
        raise LibraryError("output parent must already exist")
    fd, name = tempfile.mkstemp(prefix=".prim-publish-", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp, path)  # Fails if the destination exists; never replaces it.
    finally:
        temp.unlink(missing_ok=True)


def compile_library(root: Path) -> dict:
    root = local_path(root)
    discovered = discover_profiles(root)
    definitions = []
    for entry in discovered["profiles"]:
        folder = (root / entry["location"]).parent
        resources = {}
        declared = {"manifest": "PROFILE.md", **entry["metadata"].get("resources", {})}
        if declared["manifest"] != "PROFILE.md":
            raise ProfileError("the manifest resource must refer to PROFILE.md")
        for name, rel in declared.items():
            path = _local_path(folder, rel)
            # Declared directories are descriptive pointers, not recursive uploads.
            if path.is_dir():
                continue
            if path.suffix not in {".md", ".json"}:
                raise ProfileError("library resources must be bounded .md/.json files")
            raw = read_local(path, MAX_DOCUMENT)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ProfileError("library resources must be UTF-8") from exc
            resources[name] = {"text": text, "sha256": hashlib.sha256(raw).hexdigest()}
        item = {"metadata": entry["metadata"], "resources": resources}
        item["definition_sha256"] = fingerprint(item)
        definitions.append(item)
    result = {"format": "prim-library", "version": 1, "definitions": definitions,
              "snapshot_sha256": fingerprint(definitions)}
    Library(result, EMPTY_RANKINGS)
    return result


def publish(root: Path, output: Path, withdrawn: list | None = None) -> dict:
    from .resolution import check_source
    source = {"format": "prim-library-source", "version": 1,
              "library": compile_library(root), "withdrawn": [] if withdrawn is None else withdrawn}
    raw = canonical(source) + b"\n"
    check_source(raw)
    write_new(output, raw)
    return {"path": str(output), "sha256": hashlib.sha256(raw).hexdigest(),
            "definitions": len(source["library"]["definitions"]),
            "publisher_identity": "not_verified", "network_publication": "not_performed"}
