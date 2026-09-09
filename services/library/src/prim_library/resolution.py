"""Experimental, bounded local resolution. Hashes establish bytes, not authority."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import re
import shutil
import tempfile

from .library import Library, LibraryError, MAX_DOCUMENT, MAX_SNAPSHOT, canonical, fingerprint, load_json, version_key
from .profiles import IDENTITY, SLUG
from .publishing import EMPTY_RANKINGS, local_path, read_local, write_new

SHA = re.compile(r"[0-9a-f]{64}\Z")
NAME = re.compile(SLUG + r"\Z")
MAX_SOURCES = 16
MAX_PROFILES = 128
MAX_SOURCE = MAX_SNAPSHOT + MAX_DOCUMENT
DEPENDENCIES = "prim-library-dependencies"


def fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= set(value) or set(value) - set(required) - set(optional):
        raise LibraryError("invalid or unsupported distribution fields")


def digest(value):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise LibraryError("expected a lowercase SHA-256 digest")
    return value


def semver(value):
    if not isinstance(value, str) or len(value) > 128:
        raise LibraryError("version must be a bounded semantic version")
    return version_key(value)


def name(value):
    if not isinstance(value, str) or len(value) > 64 or not NAME.fullmatch(value):
        raise LibraryError("expected a bounded lowercase source or namespace name")


def identity(value):
    if not isinstance(value, str) or not IDENTITY.fullmatch(value) or any(len(x) > 64 for x in value.split('/')):
        raise LibraryError("full namespace/name identity is required; aliases are not resolved")


def bounded_list(value, maximum=MAX_PROFILES, nonempty=False):
    if not isinstance(value, list) or len(value) > maximum or (nonempty and not value):
        raise LibraryError("invalid or excessive distribution list")


def pin(value):
    fields(value, ["id", "version", "definition_sha256"])
    identity(value["id"])
    semver(value["version"])
    digest(value["definition_sha256"])


def requires(entry):
    extension = entry["metadata"].get("extensions", {}).get(DEPENDENCIES)
    if extension is None:
        return []
    fields(extension, ["version", "requires"])
    if type(extension["version"]) is not int or extension["version"] != 1:
        raise LibraryError("unsupported dependency declaration version")
    bounded_list(extension["requires"])
    seen = set()
    for item in extension["requires"]:
        fields(item, ["id", "version"], ["definition_sha256"])
        identity(item['id'])
        semver(item['version'])
        if 'definition_sha256' in item:
            digest(item['definition_sha256'])
        if item["id"] in seen:
            raise LibraryError("duplicate dependency identity")
        seen.add(item["id"])
    return extension["requires"]


def check_source(raw: bytes) -> dict:
    source = load_json(raw, MAX_SOURCE)
    fields(source, ["format", "version", "library", "withdrawn"])
    if source["format"] != "prim-library-source" or type(source["version"]) is not int or source["version"] != 1:
        raise LibraryError("unsupported source format/version")
    # Library retains its existing format. Validate untrusted envelope shapes here
    # before its kit readers, converting malformed structures into bounded failures.
    try:
        snapshot = source["library"]
        fields(snapshot, ["format", "version", "definitions", "snapshot_sha256"])
        if snapshot['format'] != 'prim-library' or type(snapshot['version']) is not int:
            raise LibraryError("source must contain a complete library snapshot")
        bounded_list(snapshot["definitions"], MAX_PROFILES, nonempty=True)
        for entry in snapshot["definitions"]:
            fields(entry, ["metadata", "resources", "definition_sha256"])
            metadata = entry["metadata"]
            fields(metadata, ["id", "name", "description", "version", "maturity"],
                   ["format", "manifest_version", "license", "kinds", "resources", "legacy_aliases", "extensions"])
            identity(metadata["id"])
            if metadata["maturity"] not in {"development", "alpha", "beta", "stable", "deprecated"}:
                raise LibraryError("unsupported maturity")
            for key in ["name", "description"]:
                if not isinstance(metadata[key], str) or not metadata[key].strip():
                    raise LibraryError("invalid definition metadata")
            for key in ["kinds", "legacy_aliases"]:
                values = metadata.get(key, [])
                bounded_list(values)
                for value in values:
                    name(value)
            if not isinstance(metadata.get("extensions", {}), dict) or not isinstance(entry['resources'], dict):
                raise LibraryError("invalid resources or extensions")
            for resource in entry['resources'].values():
                fields(resource, ['text', 'sha256'])
                if not isinstance(resource['text'], str) or len(resource['text'].encode('utf-8')) > MAX_DOCUMENT:
                    raise LibraryError("invalid or oversized source resource")
                digest(resource['sha256'])
            requires(entry)
        Library(snapshot, EMPTY_RANKINGS)
    except (KeyError, TypeError, AttributeError, IndexError, UnicodeError) as exc:
        raise LibraryError("malformed definition source") from exc
    bounded_list(source['withdrawn'])
    seen = set()
    for item in source['withdrawn']:
        fields(item, ['id', 'version', 'definition_sha256', 'reason'])
        pin({key: item[key] for key in ['id', 'version', 'definition_sha256']})
        if not isinstance(item['reason'], str) or not item['reason'].strip() or len(item['reason']) > 1024:
            raise LibraryError("withdrawal requires a bounded reason")
        key = (item['id'], item['version'])
        if key in seen:
            raise LibraryError("duplicate withdrawal")
        seen.add(key)
    return source


def check_request(request: dict, *, paths: bool) -> None:
    fields(request, ['format', 'version', 'sources', 'requirements', 'allow_deprecated'])
    if request['format'] != 'prim-library-request' or type(request['version']) is not int or request['version'] != 1:
        raise LibraryError("unsupported resolution request")
    if type(request['allow_deprecated']) is not bool:
        raise LibraryError("allow_deprecated must be boolean")
    bounded_list(request['sources'], MAX_SOURCES, nonempty=True)
    seen = set()
    for source in request['sources']:
        fields(source, ['name', 'sha256', 'namespaces', 'visibility'] + (['path'] if paths else []))
        name(source['name'])
        if source['name'] in seen:
            raise LibraryError("duplicate source name")
        seen.add(source['name'])
        digest(source['sha256'])
        bounded_list(source['namespaces'], MAX_PROFILES, nonempty=True)
        for namespace in source['namespaces']:
            name(namespace)
        if len(set(source['namespaces'])) != len(source['namespaces']):
            raise LibraryError("duplicate namespace")
        if not isinstance(source['visibility'], str) or source['visibility'] not in {'public', 'private'}:
            raise LibraryError("source visibility must be public or private")
        if paths and (not isinstance(source['path'], str) or not source['path'] or '\0' in source['path'] or '://' in source['path']):
            raise LibraryError("source path must be an explicit local path")
    bounded_list(request['requirements'], nonempty=True)
    seen = set()
    for item in request['requirements']:
        identity(item.get('id') if isinstance(item, dict) else None)
        if item['id'] in seen:
            raise LibraryError("duplicate root requirement")
        seen.add(item['id'])
        if 'version' in item:
            fields(item, ['id', 'version'], ['definition_sha256'])
            semver(item['version'])
            if 'definition_sha256' in item:
                digest(item['definition_sha256'])
        else:
            fields(item, ['id', 'minimum', 'before', 'allow_prerelease'])
            low, high = semver(item['minimum']), semver(item['before'])
            if low >= high or type(item['allow_prerelease']) is not bool:
                raise LibraryError("invalid bounded version interval")


def resolve_data(request: dict, blobs: dict[str, bytes]) -> tuple[dict, dict]:
    """Pure resolution over already acquired pinned bytes. No ambient sources."""
    check_request(request, paths=False)
    entries, origins, withdrawn = {}, {}, set()
    for source in sorted(request['sources'], key=lambda x: x['name']):
        raw = blobs.get(source['sha256'])
        if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise LibraryError("missing or corrupt source; no network fallback")
        data = check_source(raw)
        for item in data['withdrawn']:
            if item['id'].split('/')[0] not in source['namespaces']:
                raise LibraryError("withdrawal outside the configured source namespaces")
            withdrawn.add((item['id'], item['version'], item['definition_sha256']))
        for entry in data['library']['definitions']:
            metadata = entry['metadata']
            if metadata['id'].split('/')[0] not in source['namespaces']:
                raise LibraryError("definition outside the configured source namespaces")
            key = metadata['id'], metadata['version']
            if key in entries and entries[key]['definition_sha256'] != entry['definition_sha256']:
                raise LibraryError("conflicting bytes for the same identity/version; source order cannot choose authority")
            entries[key] = entry
            origins.setdefault(key, []).append(source['name'])
    if len(entries) > MAX_PROFILES:
        raise LibraryError("combined source definition limit exceeded")
    for profile_id, version, sha in withdrawn:
        entry = entries.get((profile_id, version))
        if entry is not None and entry['definition_sha256'] != sha:
            raise LibraryError("withdrawn identity/version cannot be republished with different bytes")
    selected, visiting = {}, set()

    def choose(requirement):
        candidates = []
        for (profile_id, version), entry in entries.items():
            if profile_id != requirement['id']:
                continue
            if (profile_id, version, entry['definition_sha256']) in withdrawn:
                continue
            if entry['metadata']['maturity'] == 'deprecated' and not request['allow_deprecated']:
                continue
            if 'version' in requirement:
                if version != requirement['version']:
                    continue
                if requirement.get('definition_sha256', entry['definition_sha256']) != entry['definition_sha256']:
                    continue
            else:
                key = semver(version)
                if not semver(requirement['minimum']) <= key < semver(requirement['before']):
                    continue
                if not requirement['allow_prerelease'] and not key[3]:
                    continue
            candidates.append(entry)
        if not candidates:
            raise LibraryError("no permitted definition satisfies a requirement; no fallback or silent upgrade")
        candidates.sort(key=lambda x: semver(x['metadata']['version']), reverse=True)
        if len(candidates) > 1 and semver(candidates[0]['metadata']['version']) == semver(candidates[1]['metadata']['version']):
            raise LibraryError("ambiguous equal-precedence builds; request an exact version")
        return candidates[0]

    def visit(requirement):
        entry = choose(requirement)
        profile_id, version = entry['metadata']['id'], entry['metadata']['version']
        if profile_id in visiting:
            raise LibraryError("dependency cycle")
        if profile_id in selected:
            if selected[profile_id]['definition_sha256'] != entry['definition_sha256']:
                raise LibraryError("incompatible dependency pins; one version per identity is required")
            return
        if len(visiting) >= 32:
            raise LibraryError("dependency depth limit exceeded")
        visiting.add(profile_id)
        for dependency in sorted(requires(entry), key=lambda x: x['id']):
            visit(dependency)
        visiting.remove(profile_id)
        selected[profile_id] = entry

    # Resolve exact constraints before ranges so a range can reuse an already
    # selected compatible pin, without an exponential backtracking solver.
    roots = sorted(request['requirements'], key=lambda x: ('version' not in x, x['id']))
    for requirement in roots:
        if requirement['id'] in selected and 'version' not in requirement:
            entry = selected[requirement['id']]
            key = semver(entry['metadata']['version'])
            if (semver(requirement['minimum']) <= key < semver(requirement['before'])
                    and (requirement['allow_prerelease'] or key[3])):
                continue
        visit(requirement)
    definitions = [selected[key] for key in sorted(selected)]
    snapshot = {'format': 'prim-library', 'version': 1, 'definitions': definitions,
                'snapshot_sha256': fingerprint(definitions)}
    Library(snapshot, EMPTY_RANKINGS)
    clean = deepcopy(request)
    clean['sources'].sort(key=lambda x: x['name'])
    for source in clean['sources']:
        source['namespaces'].sort()
    clean['requirements'].sort(key=lambda x: x['id'])
    lock = {'format': 'prim-resolution-lock', 'version': 1, 'request': clean,
            'snapshot_sha256': snapshot['snapshot_sha256'],
            'visibility': 'private' if any(s['visibility'] == 'private' for s in clean['sources']) else 'public',
            'publisher_identity': 'not_verified',
            'definitions': [{'id': e['metadata']['id'], 'version': e['metadata']['version'],
                             'definition_sha256': e['definition_sha256'], 'maturity': e['metadata']['maturity'],
                             'sources': origins[(e['metadata']['id'], e['metadata']['version'])]}
                            for e in definitions]}
    return lock, snapshot


def write_bundle(output: Path, lock: dict, snapshot: dict, blobs: dict) -> dict:
    output = local_path(output)
    if output.exists() or not output.parent.is_dir():
        raise LibraryError("bundle output must be a new directory under an existing parent")
    temp = Path(tempfile.mkdtemp(prefix='.prim-resolve-', dir=output.parent))
    raw_lock = canonical(lock) + b'\n'
    try:
        if len(raw_lock) > MAX_DOCUMENT:
            raise LibraryError('resolution lock size limit exceeded')
        (temp / 'sources').mkdir(mode=0o700)
        for sha in sorted({s['sha256'] for s in lock['request']['sources']}):
            digest(sha)
            write_new(temp / 'sources' / (sha + '.json'), blobs[sha])
        write_new(temp / 'prim-library.lock.json', raw_lock)
        write_new(temp / 'library.json', canonical(snapshot) + b'\n')
        if output.exists() or output.is_symlink():
            raise LibraryError("bundle destination appeared during creation")
        temp.rename(output)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return {'path': str(output), 'lock_sha256': hashlib.sha256(raw_lock).hexdigest(),
            'snapshot_sha256': snapshot['snapshot_sha256'], 'definitions': len(lock['definitions']),
            'visibility': lock['visibility'], 'publisher_identity': 'not_verified'}


def resolve_file(request_path: Path, output: Path) -> dict:
    request_path = local_path(request_path)
    request = load_json(read_local(request_path, MAX_DOCUMENT))
    check_request(request, paths=True)
    clean, blobs = deepcopy(request), {}
    for source in clean['sources']:
        path = Path(source.pop('path'))
        if not path.is_absolute():
            path = request_path.parent / path
        blobs[source['sha256']] = read_local(path, MAX_SOURCE)
        if hashlib.sha256(blobs[source['sha256']]).hexdigest() != source['sha256']:
            raise LibraryError("source digest mismatch")
    lock, snapshot = resolve_data(clean, blobs)
    return write_bundle(output, lock, snapshot, blobs)


def restore(lock_path: Path, cache: Path, output: Path, expected_sha256: str) -> dict:
    digest(expected_sha256)
    raw = read_local(lock_path, MAX_DOCUMENT)
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise LibraryError("lock digest mismatch")
    lock = load_json(raw)
    fields(lock, ['format', 'version', 'request', 'snapshot_sha256', 'visibility', 'publisher_identity', 'definitions'])
    if lock['format'] != 'prim-resolution-lock' or type(lock['version']) is not int or lock['version'] != 1:
        raise LibraryError("unsupported resolution lock")
    check_request(lock['request'], paths=False)
    blobs = {s['sha256']: read_local(cache / (s['sha256'] + '.json'), MAX_SOURCE) for s in lock['request']['sources']}
    expected_lock, snapshot = resolve_data(lock['request'], blobs)
    if canonical(lock) != canonical(expected_lock):
        raise LibraryError("lock does not reproduce the pinned resolution")
    return write_bundle(output, lock, snapshot, blobs)
