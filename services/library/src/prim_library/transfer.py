"""Bounded, byte-preserving complete-pack ZIP transport. Never extracts or executes code."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import tempfile
import zlib

from .library import LibraryError, MAX_DOCUMENT, canonical, load_json
from .publishing import local_path, read_local, write_new

MANIFEST = 'prim-transfer.json'
MAX_FILES = 256
MAX_FILE = 16 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024
MAX_ARCHIVE = 34 * 1024 * 1024
LOCK = 'prim-definition.lock.json'
PATH = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,119}(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,119}){0,7}\Z')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def names_valid(names):
    folded = set()
    for name in names:
        if not isinstance(name, str) or len(name) > 240 or not PATH.fullmatch(name):
            raise LibraryError('unsupported portable pack path; names are never silently rewritten')
        parts = name.split('/')
        if any(p.endswith('.') or p.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))} for p in parts):
            raise LibraryError('nonportable pack path')
        lower = name.lower()
        if lower in folded:
            raise LibraryError('duplicate or case-colliding pack path')
        folded.add(lower)
    for name in folded:
        parts = name.split('/')
        if any('/'.join(parts[:i]) in folded for i in range(1, len(parts))):
            raise LibraryError('file/directory path collision')


def pin_from(files):
    if LOCK not in files or 'index.md' not in files:
        raise LibraryError('complete pack requires its definition lock and index.md')
    pin = load_json(files[LOCK])
    if not isinstance(pin, dict) or set(pin) != {'profile_id', 'version', 'definition_sha256'}:
        raise LibraryError('invalid exact definition lock')
    if not isinstance(pin['profile_id'], str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}/[a-z][a-z0-9-]{0,63}', pin['profile_id']):
        raise LibraryError('invalid profile identity')
    if not isinstance(pin['version'], str) or not re.fullmatch(r'[0-9A-Za-z.+-]{1,128}', pin['version']):
        raise LibraryError('invalid profile version')
    if not isinstance(pin['definition_sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', pin['definition_sha256']):
        raise LibraryError('invalid definition digest')
    # Captured Research references are part of this transport's declared support.
    # Other unknown files and profiles remain opaque, preserved bytes.
    if pin['profile_id'] == 'primfoundation/research':
        if 'research.json' not in files:
            raise LibraryError('missing authoritative Research record')
        record = load_json(files['research.json'])
        if not isinstance(record, dict) or not isinstance(record.get('sources', []), list):
            raise LibraryError('invalid Research sources')
        for source in record.get('sources', []):
            if not isinstance(source, dict) or 'artifact' not in source:
                continue
            artifact = source['artifact']
            if not isinstance(artifact, dict) or not isinstance(artifact.get('path'), str):
                raise LibraryError('invalid embedded artifact reference')
            raw = files.get(artifact['path'])
            if raw is None or type(artifact.get('bytes')) is not int or len(raw) != artifact['bytes'] or sha(raw) != artifact.get('sha256'):
                raise LibraryError('missing or changed embedded artifact; no incomplete export')
    return pin


def inventory(files):
    if not 2 <= len(files) <= MAX_FILES or any(n.lower() == MANIFEST for n in files):
        raise LibraryError('pack file count or reserved transfer-manifest collision')
    names_valid(files)
    total = 0
    for name, raw in files.items():
        if not isinstance(raw, bytes) or len(raw) > MAX_FILE:
            raise LibraryError('pack file byte limit exceeded')
        total += len(raw)
    if total > MAX_TOTAL:
        raise LibraryError('complete pack total byte limit exceeded')
    return {'definition': pin_from(files), 'files': [{'bytes': len(files[n]), 'path': n, 'sha256': sha(files[n])} for n in sorted(files)],
            'format': 'prim-complete-pack', 'version': 1}


def encode_files(files):
    """Encode ordinary ZIP STORE entries with a canonical SHA-256 file inventory."""
    manifest = canonical(inventory(files)) + b'\n'
    if len(manifest) > MAX_DOCUMENT:
        raise LibraryError('transfer manifest byte limit exceeded')
    entries = [(MANIFEST, manifest), *sorted(files.items())]
    local, central = bytearray(), bytearray()
    for name, raw in entries:
        name_bytes = name.encode('ascii'); crc = zlib.crc32(raw); offset = len(local)
        local += struct.pack('<IHHHHHIIIHH', 0x04034b50, 20, 0x800, 0, 0, 33, crc, len(raw), len(raw), len(name_bytes), 0)
        local += name_bytes + raw
        central += struct.pack('<IHHHHHHIIIHHHHHII', 0x02014b50, 0x0314, 20, 0x800, 0, 0, 33, crc, len(raw), len(raw), len(name_bytes), 0, 0, 0, 0, 0o100600 << 16, offset)
        central += name_bytes
    result = bytes(local + central + struct.pack('<IHHHHIIH', 0x06054b50, 0, 0, len(entries), len(entries), len(central), len(local), 0))
    if len(result) > MAX_ARCHIVE:
        raise LibraryError('complete archive byte limit exceeded')
    return result


def decode_files(raw, expected_sha256=None):
    """Reject unsupported ZIP forms before materializing any file on disk."""
    fail = lambda: LibraryError('invalid complete pack: compressed, encrypted, linked, ambiguous or corrupt entries are refused')
    if not isinstance(raw, bytes) or not 22 <= len(raw) <= MAX_ARCHIVE:
        raise fail()
    if expected_sha256 is not None and (not isinstance(expected_sha256, str) or not re.fullmatch('[0-9a-f]{64}', expected_sha256) or sha(raw) != expected_sha256):
        raise LibraryError('complete archive digest mismatch')
    end = len(raw) - 22
    sig, disk, cd_disk, count_disk, count, size, start, comment = struct.unpack_from('<IHHHHIIH', raw, end)
    if sig != 0x06054b50 or disk or cd_disk or count != count_disk or not 3 <= count <= MAX_FILES + 1 or comment or start + size != end:
        raise fail()
    files = {}; local = 0; central = start; total = 0
    for _ in range(count):
        if central + 46 > end:
            raise fail()
        c = struct.unpack_from('<IHHHHHHIIIHHHHHII', raw, central)
        sig, made, needed, flags, method, clock, date, crc, compressed, length, name_len, extra, comment, disk, internal, external, offset = c
        if sig != 0x02014b50 or made != 0x0314 or needed != 20 or flags != 0x800 or method or compressed != length or length > MAX_FILE or extra or comment or disk or internal or external != 0o100600 << 16 or offset != local or central + 46 + name_len > end or local + 30 + name_len + length > start:
            raise fail()
        name_raw = raw[central+46:central+46+name_len]
        try:
            name = name_raw.decode('ascii')
        except UnicodeError as exc:
            raise fail() from exc
        if name in files:
            raise fail()
        h = struct.unpack_from('<IHHHHHIIIHH', raw, local)
        if h != (0x04034b50, needed, flags, method, clock, date, crc, compressed, length, name_len, 0) or raw[local+30:local+30+name_len] != name_raw:
            raise fail()
        data = raw[local+30+name_len:local+30+name_len+length]
        if zlib.crc32(data) != crc:
            raise fail()
        files[name] = data; total += length
        if total > MAX_TOTAL + MAX_DOCUMENT:
            raise fail()
        local += 30 + name_len + length; central += 46 + name_len
    if local != start or central != end or MANIFEST not in files:
        raise fail()
    names_valid(files)
    manifest_raw = files.pop(MANIFEST)
    manifest = load_json(manifest_raw)
    expected = inventory(files)
    if manifest != expected or manifest_raw != canonical(expected) + b'\n':
        raise LibraryError('complete pack inventory or digest mismatch')
    return files, {'archive_sha256': sha(raw), 'manifest_sha256': sha(manifest_raw), 'files': len(files),
                   'total_bytes': sum(len(v) for v in files.values()), 'pin': expected['definition'],
                   'integrity': 'passed', 'source_authentication': 'not_verified', 'content_execution': 'not_performed'}


def read_folder(source):
    source = local_path(source)
    if not source.is_dir():
        raise LibraryError('select a local pack directory')
    files = {}; directories = 0
    for parent, dirs, names in os.walk(source, followlinks=False):
        directories += len(dirs)
        if directories > MAX_FILES:
            raise LibraryError('pack directory count limit exceeded')
        for name in dirs:
            if (Path(parent) / name).is_symlink():
                raise LibraryError('symlink directories are not transported')
        for name in names:
            path = Path(parent) / name
            rel = path.relative_to(source).as_posix()
            names_valid([rel])
            if len(files) >= MAX_FILES:
                raise LibraryError('pack file count limit exceeded')
            before = path.lstat()
            if not stat.S_ISREG(before.st_mode):
                raise LibraryError('only regular pack files may be transported')
            data = read_local(path, min(MAX_FILE, MAX_TOTAL-sum(len(v) for v in files.values())))
            after = path.lstat()
            if (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise LibraryError('pack source changed during read')
            files[rel] = data
    inventory(files)
    return files


def export_pack(source, target):
    source, target = local_path(source), local_path(target)
    if source == target or source in target.parents:
        raise LibraryError('export destination must be outside the source pack')
    files = read_folder(source); raw = encode_files(files)
    _, result = decode_files(raw)
    write_new(target, raw)  # Atomic, exclusive publication through the shared writer.
    return {'status': 'exported', **result}


def import_pack(archive, target, expected_sha256=None):
    archive, target = local_path(archive), local_path(target)
    files, result = decode_files(read_local(archive, MAX_ARCHIVE), expected_sha256)
    if target.exists() or not target.parent.is_dir():
        raise LibraryError('import requires a new directory under an existing trusted parent')
    temp = Path(tempfile.mkdtemp(prefix='.prim-transfer-', dir=target.parent))
    try:
        for name, raw in files.items():
            path = temp / name; path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            write_new(path, raw)
        if target.exists() or target.is_symlink():
            raise LibraryError('import destination appeared during creation')
        temp.rename(target)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return {'status': 'imported', **result}
