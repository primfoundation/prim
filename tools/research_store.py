"""Bounded, byte-preserving local ORF transport. NOT a Research vNext encoding.

Only regular files/directories from a trusted, non-mutating local filesystem.
No networking, archive extraction, source execution, or overwrite of destinations.
File bytes, relative names, and empty directories survive; OS metadata does not.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import unicodedata
from typing import Any

MAX_FILES = 1024
MAX_ENTRIES = 2048
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024
MAX_JSON_BYTES = 24 * 1024 * 1024
MAX_DEPTH = 16
FORMAT = 'prim-orf-preservation'
LOSSES = [
    'File contents, relative paths and empty directories are preserved.',
    'Permissions, executable bits, owners, timestamps, extended attributes and original archive bytes are not preserved.',
    'This is a preservation transport, not semantic migration to Research vNext.',
    'Digests detect changes; they do not authenticate a publisher, authorize work or prove claims.',
]


class ResearchError(ValueError):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def relative_path(name: Any) -> str:
    if not isinstance(name, str) or not name or len(name.encode('utf-8')) > 1024:
        raise ResearchError('invalid or oversized relative path')
    if unicodedata.normalize('NFC', name) != name or any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise ResearchError('noncanonical or control-character path')
    if any(c in name for c in '\\:<>"|?*') or PurePosixPath(name).is_absolute():
        raise ResearchError('path must be a portable relative POSIX path')
    parts = name.split('/')
    if len(parts) > MAX_DEPTH:
        raise ResearchError('path depth limit exceeded')
    for part in parts:
        if part in {'', '.', '..'} or part != part.strip() or part.endswith('.') or part.casefold() == '.git':
            raise ResearchError('unsafe or noncanonical path component')
        if re.fullmatch(r'(con|prn|aux|nul|com[1-9]|lpt[1-9])', part.split('.')[0], re.I):
            raise ResearchError('reserved filesystem name')
    return name


def real_local(path: Path) -> Path:
    """Reject symlinks on the supplied path, including intermediate components."""
    absolute = Path(os.path.abspath(path))
    for candidate in [*reversed(absolute.parents), absolute]:
        if candidate.is_symlink():
            raise ResearchError('symlink path is not supported')
    return absolute


def read_regular(path: Path, maximum: int) -> bytes:
    path = real_local(path)
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise ResearchError('input must be a regular file')
            if info.st_size > maximum:
                raise ResearchError('file size limit exceeded')
            raw = stream.read(maximum + 1)
            if len(raw) > maximum:
                raise ResearchError('file size limit exceeded')
            return raw
    except OSError as exc:
        raise ResearchError(f'cannot read local file: {path.name}') from exc


def _layout(files: dict[str, bytes], directories: list[str]) -> None:
    if len(files) > MAX_FILES or len(files) + len(directories) > MAX_ENTRIES:
        raise ResearchError('entry count limit exceeded')
    if sum(map(len, files.values())) > MAX_TOTAL_BYTES:
        raise ResearchError('total byte limit exceeded')
    all_names = [*files, *directories]
    if len(set(all_names)) != len(all_names):
        raise ResearchError('duplicate file/directory entry')
    seen: set[str] = set()
    dirs = set(directories)
    for name in all_names:
        relative_path(name)
        if name.casefold() in seen:
            raise ResearchError('case-colliding path')
        seen.add(name.casefold())
        parts = name.split('/')
        for i in range(1, len(parts)):
            if '/'.join(parts[:i]) not in dirs:
                raise ResearchError('missing parent directory or file/directory collision')
    if any(len(raw) > MAX_FILE_BYTES for raw in files.values()):
        raise ResearchError('file size limit exceeded')


def read_directory(location: Path) -> tuple[dict[str, bytes], list[str]]:
    root = real_local(location)
    if not root.is_dir():
        raise ResearchError('expected a directory pack; archives are not supported in this slice')
    files: dict[str, bytes] = {}
    dirs: list[str] = []
    visited = 0
    total = 0

    def walk(folder: Path) -> None:
        nonlocal visited, total
        try:
            entries = []
            with os.scandir(folder) as iterator:
                for entry in iterator:
                    visited += 1
                    if visited > MAX_ENTRIES:
                        raise ResearchError('entry count limit exceeded')
                    entries.append(entry)
            for entry in sorted(entries, key=lambda e: e.name):
                path = Path(entry.path)
                rel = relative_path(path.relative_to(root).as_posix())
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISDIR(mode):
                    dirs.append(rel)
                    walk(path)
                elif stat.S_ISREG(mode):
                    raw = read_regular(path, min(MAX_FILE_BYTES, MAX_TOTAL_BYTES - total))
                    total += len(raw)
                    files[rel] = raw
                    if len(files) > MAX_FILES:
                        raise ResearchError('file count limit exceeded')
                else:
                    raise ResearchError('symlinks and special files are not supported')
        except OSError as exc:
            raise ResearchError('directory could not be read completely') from exc
    walk(root)
    _layout(files, dirs)
    return files, sorted(dirs)


def payload_id(files: dict[str, bytes], directories: list[str]) -> str:
    _layout(files, directories)
    return digest(canonical({'directories': sorted(directories), 'files': [
        {'path': p, 'bytes': len(b), 'sha256': digest(b)} for p, b in sorted(files.items())
    ]}))


def preserve(files: dict[str, bytes], directories: list[str]) -> dict[str, Any]:
    return {
        'format': FORMAT, 'version': 1,
        'payload_sha256': payload_id(files, directories),
        'directories': sorted(directories),
        'files': [{'path': p, 'sha256': digest(b), 'data_base64': base64.b64encode(b).decode('ascii')}
                  for p, b in sorted(files.items())],
        'preservation_scope': LOSSES,
    }


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ResearchError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def load_transport(path: Path) -> tuple[dict[str, bytes], list[str]]:
    raw = read_regular(path, MAX_JSON_BYTES)
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique,
                           parse_constant=lambda _: (_ for _ in ()).throw(ResearchError('nonfinite JSON')))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ResearchError('invalid preservation JSON') from exc
    if not isinstance(value, dict) or set(value) != {'format', 'version', 'payload_sha256', 'directories', 'files', 'preservation_scope'}:
        raise ResearchError('unsupported preservation fields')
    if value['format'] != FORMAT or type(value['version']) is not int or value['version'] != 1:
        raise ResearchError('unsupported preservation format/version')
    if value['preservation_scope'] != LOSSES:
        raise ResearchError('unsupported preservation scope')
    rows, dirs = value['files'], value['directories']
    if not isinstance(rows, list) or len(rows) > MAX_FILES or not isinstance(dirs, list) or len(rows) + len(dirs) > MAX_ENTRIES:
        raise ResearchError('invalid file/directory inventory')
    for directory in dirs:
        relative_path(directory)
    files: dict[str, bytes] = {}
    total = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'path', 'sha256', 'data_base64'}:
            raise ResearchError('invalid preserved file record')
        name = relative_path(row['path'])
        if name in files:
            raise ResearchError('duplicate preserved file')
        data = row['data_base64']
        if not isinstance(data, str) or len(data) > ((MAX_FILE_BYTES + 2) // 3) * 4:
            raise ResearchError('encoded file size limit exceeded')
        try:
            b = base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ResearchError('invalid base64 file bytes') from exc
        total += len(b)
        if total > MAX_TOTAL_BYTES:
            raise ResearchError('total byte limit exceeded')
        if digest(b) != row['sha256']:
            raise ResearchError('preserved file digest mismatch')
        files[name] = b
    if payload_id(files, dirs) != value['payload_sha256']:
        raise ResearchError('preserved payload digest mismatch')
    return files, sorted(dirs)


def load_input(path: Path) -> tuple[dict[str, bytes], list[str]]:
    path = real_local(path)
    return read_directory(path) if path.is_dir() else load_transport(path)


def write_new_file(path: Path, raw: bytes) -> None:
    path = real_local(path)
    try:
        with path.open('xb') as stream:
            stream.write(raw)
    except OSError as exc:
        raise ResearchError('output must be a new file in an existing trusted directory') from exc


def restore(files: dict[str, bytes], dirs: list[str], target: Path) -> None:
    _layout(files, dirs)
    target = real_local(target)
    if target.exists() or not target.parent.is_dir():
        raise ResearchError('restore needs a new destination in an existing trusted directory')
    temp = Path(tempfile.mkdtemp(prefix='.prim-restore-', dir=target.parent))
    try:
        for name in sorted(dirs, key=lambda p: (len(p.split('/')), p)):
            (temp / name).mkdir()
        for name, raw in files.items():
            (temp / name).write_bytes(raw)
        # Supported context is non-mutating. Recheck instead of overwriting existing work.
        if target.exists() or target.is_symlink():
            raise ResearchError('restore destination appeared during operation')
        temp.rename(target)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
