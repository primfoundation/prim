"""Explicit local artifact capture into a new Research draft. No extraction/network."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import unicodedata

from .cli import create
from .library import LibraryError, MAX_DOCUMENT, canonical, fingerprint, load_json
from .pack import read_pack
from .publishing import local_path, read_local, write_new
from .resolution import digest, fields

PROFILE = 'primfoundation/research'
MAX_SOURCES = 128
MAX_ARTIFACT = 4 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024
TOKEN = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}\Z')
CHECKS = {'byte_preservation': 'passed', 'definition_structure': 'passed',
          'authorization': 'recorded_not_verified', 'factual_accuracy': 'not_checked',
          'content_extraction': 'not_performed', 'network': 'not_used',
          'visibility': 'private', 'recursive_expansion': 'not_performed'}


def text(value, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or '\0' in value:
        raise LibraryError('capture requires bounded nonempty text')


def token(value):
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise LibraryError('capture requires a bounded source or operation identifier')


def portable_metadata(value):
    if type(value) in (int, float) and abs(value) > 2**53 - 1:
        raise LibraryError('capture metadata numbers exceed the portable host range; use an explicit string')
    if isinstance(value, dict):
        for key, child in value.items():
            if unicodedata.normalize('NFC', key) != key:
                raise LibraryError('capture metadata requires NFC object keys; no silent normalization')
            portable_metadata(child)
    elif isinstance(value, list):
        for child in value:
            portable_metadata(child)


def check_manifest(value):
    fields(value, ['format', 'version', 'operation_id', 'title', 'question', 'sources'], ['extensions'])
    if value['format'] != 'prim-artifact-capture' or type(value['version']) is not int or value['version'] != 1:
        raise LibraryError('unsupported artifact capture format/version')
    portable_metadata(value)
    token(value['operation_id'])
    text(value['title'], 256)
    if value['question'] is not None:
        text(value['question'], 4096)
    if not isinstance(value.get('extensions', {}), dict):
        raise LibraryError('capture extensions must be an object')
    sources = value['sources']
    if not isinstance(sources, list) or not 1 <= len(sources) <= MAX_SOURCES:
        raise LibraryError('capture requires 1 to 128 explicitly selected files')
    seen = set()
    for source in sources:
        fields(source, ['id', 'path', 'locator', 'sha256', 'media_type', 'observed_at', 'permissions'], ['extensions'])
        token(source['id'])
        if source['id'] in seen:
            raise LibraryError('duplicate source identity; byte deduplication does not merge identities')
        seen.add(source['id'])
        text(source['path'], 4096)
        if '://' in source['path']:
            raise LibraryError('capture reads explicit local files, never source URLs')
        text(source['locator'], 4096)
        digest(source['sha256'])
        if not isinstance(source['media_type'], str) or len(source['media_type']) > 128 or not re.fullmatch(r'[a-z0-9.+-]+/[a-z0-9.+-]+', source['media_type']):
            raise LibraryError('media_type must be an explicitly recorded type/subtype')
        observed = source['observed_at']
        if observed is not None:
            text(observed, 64)
            try:
                date = datetime.fromisoformat(observed)
                if date.utcoffset() is None:
                    raise ValueError('missing timezone')
            except ValueError as exc:
                raise LibraryError('observed_at must be null or a timezone-aware ISO timestamp') from exc
        permissions = source['permissions']
        fields(permissions, ['may_store', 'may_share', 'basis_as_recorded'])
        if permissions['may_store'] is not True or type(permissions['may_share']) is not bool:
            raise LibraryError('capture requires an explicit recorded grant to store; sharing must be boolean')
        text(permissions['basis_as_recorded'], 2048)
        if not isinstance(source.get('extensions', {}), dict):
            raise LibraryError('source extensions must be an object')


def clean_manifest(value):
    result = deepcopy(value)
    for source in result['sources']:
        del source['path']
    result['sources'].sort(key=lambda source: source['id'])
    return result


def read_artifact(path, maximum):
    path = local_path(path)
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(path, flags), 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
            raise LibraryError('capture source must be a bounded regular file')
        raw = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    if len(raw) > maximum:
        raise LibraryError('capture byte quota exceeded')
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise LibraryError('source changed during capture; retry from a stable snapshot')
    return raw, {'mtime_ns_as_observed': str(before.st_mtime_ns),
                 'posix_mode_as_observed': stat.S_IMODE(before.st_mode)}


def inventory(folder, blobs):
    names = ['research.json', 'prim-definition.lock.json', 'index.md', 'log.md']
    names += ['artifacts/' + sha + '.bin' for sha in sorted(blobs)]
    result = []
    for name in names:
        raw = read_local(folder / name, MAX_ARTIFACT if name.startswith('artifacts/') else MAX_DOCUMENT)
        result.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    return result


def replay(library, version, output, operation_sha256):
    receipt_raw = read_local(output / 'ingestion-receipt.json', MAX_DOCUMENT)
    receipt = load_json(receipt_raw)
    fields(receipt, ['format', 'version', 'operation_sha256', 'request', 'profile', 'captured_at',
                     'sources', 'inventory', 'inventory_sha256', 'checks'])
    if receipt['format'] != 'prim-ingestion-receipt' or type(receipt['version']) is not int or receipt['version'] != 1:
        raise LibraryError('existing output is not a supported capture')
    if receipt['checks'] != CHECKS:
        raise LibraryError('unsupported capture checks; receipt cannot assert verified authority or facts')
    if receipt['operation_sha256'] != operation_sha256:
        raise LibraryError('capture operation conflict; choose a new destination')
    expected_pin = {'profile_id': PROFILE, 'version': version,
                    'definition_sha256': library.get(PROFILE, version)['definition_sha256']}
    if receipt['profile'] != expected_pin:
        raise LibraryError('capture definition pin changed')
    if fingerprint({'request': receipt['request'], 'profile': expected_pin}) != operation_sha256:
        raise LibraryError('capture request receipt was altered')
    restored_manifest = deepcopy(receipt['request'])
    fields(restored_manifest, ['format', 'version', 'operation_id', 'title', 'question', 'sources'], ['extensions'])
    if not isinstance(restored_manifest['sources'], list) or not 1 <= len(restored_manifest['sources']) <= MAX_SOURCES:
        raise LibraryError('invalid capture source inventory')
    for source in restored_manifest['sources']:
        fields(source, ['id', 'locator', 'sha256', 'media_type', 'observed_at', 'permissions'], ['extensions'])
        source['path'] = 'offline-source'
    check_manifest(restored_manifest)
    # Paths are constructed from the approved request digests, never from an
    # untrusted inventory entry. This also bounds all reads during retry.
    blobs = {s['sha256'] for s in receipt['request']['sources']}
    sizes, total = {}, 0
    for sha in blobs:
        digest(sha)
        raw = read_local(output / 'artifacts' / (sha+'.bin'), min(MAX_ARTIFACT, MAX_TOTAL-total))
        total += len(raw)
        sizes[sha] = len(raw)
        if hashlib.sha256(raw).hexdigest() != sha:
            raise LibraryError('captured artifact was altered')
    if sum(sizes[s['sha256']] for s in receipt['request']['sources']) > MAX_TOTAL:
        raise LibraryError('capture total input quota exceeded')
    observed = inventory(output, blobs)
    if observed != receipt['inventory'] or fingerprint(observed) != receipt['inventory_sha256']:
        raise LibraryError('capture files changed; retry will not overwrite subsequent work')
    checked = read_pack(library, output)
    if checked['pin'] != expected_pin or checked['validation']['status'] != 'passed':
        raise LibraryError('captured Prim no longer passes its exact definition')
    record_sources = checked['record'].get('sources', [])
    if len(record_sources) != len(receipt['request']['sources']):
        raise LibraryError('capture source count changed')
    expected_sources = []
    for request_source, record_source in zip(receipt['request']['sources'], record_sources):
        if request_source['id'] != record_source.get('id') or record_source.get('accessed_at') != receipt['captured_at']:
            raise LibraryError('capture source identity or timestamp changed')
        expected_sources.append({**request_source, 'artifact': record_source.get('artifact')})
    if expected_sources != receipt['sources']:
        raise LibraryError('capture source receipt changed')
    return {'status': 'replayed', 'path': str(output), 'operation_sha256': operation_sha256,
            'receipt_sha256': hashlib.sha256(receipt_raw).hexdigest(), 'sources': len(receipt['request']['sources']),
            'unique_artifacts': len(blobs), 'claims_created': 0, 'authorization': 'recorded_not_verified'}


def check_capture(library, output, expected_sha256):
    """Verify a transferred complete folder against an independently retained receipt pin."""
    digest(expected_sha256)
    output = local_path(output)
    raw = read_local(output / 'ingestion-receipt.json', MAX_DOCUMENT)
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise LibraryError('capture receipt digest mismatch')
    receipt = load_json(raw)
    if not isinstance(receipt, dict) or not isinstance(receipt.get('profile'), dict):
        raise LibraryError('invalid capture receipt')
    fields(receipt['profile'], ['profile_id', 'version', 'definition_sha256'])
    if not isinstance(receipt['profile']['version'], str):
        raise LibraryError('invalid capture version')
    result = replay(library, receipt['profile']['version'], output, receipt.get('operation_sha256'))
    result['status'] = 'passed'
    return result


def capture_research(library, version, manifest_path, output):
    manifest_path, output = local_path(manifest_path), local_path(output)
    manifest = load_json(read_local(manifest_path, MAX_DOCUMENT))
    check_manifest(manifest)
    profile = {'profile_id': PROFILE, 'version': version,
               'definition_sha256': library.get(PROFILE, version)['definition_sha256']}
    if library.kit(PROFILE, version)['authority_file'] != 'research.json':
        raise LibraryError('capture requires the native research.json authority contract')
    request = clean_manifest(manifest)
    operation_sha256 = fingerprint({'request': request, 'profile': profile})
    if output.exists():
        return replay(library, version, output, operation_sha256)
    if not output.parent.is_dir():
        raise LibraryError('capture output parent must already exist')
    blobs, sources, total = {}, [], 0
    for source in sorted(manifest['sources'], key=lambda row: row['id']):
        path = Path(source['path'])
        if not path.is_absolute():
            path = manifest_path.parent / path
        raw, filesystem = read_artifact(path, min(MAX_ARTIFACT, MAX_TOTAL-total))
        total += len(raw)  # Bound total input work, even for duplicate bytes.
        if hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise LibraryError('capture source digest mismatch; no partial Prim created')
        blobs[source['sha256']] = raw
        row = deepcopy(source); del row['path']
        row['artifact'] = {'path': 'artifacts/' + source['sha256'] + '.bin', 'bytes': len(raw),
                           'sha256': source['sha256'], **filesystem}
        sources.append(row)
    captured_at = datetime.now(timezone.utc).isoformat()
    record_sources = [{'id': row['id'], 'locator': row['locator'], 'kind': 'artifact',
                       'accessed_at': captured_at, 'observed_at_as_recorded': row['observed_at'],
                       'media_type_as_recorded': row['media_type'], 'permissions_as_recorded': row['permissions'],
                       'artifact': row['artifact'], 'capture_extensions': row.get('extensions', {})} for row in sources]
    values = {'id': 'capture-' + operation_sha256[:32], 'title': manifest['title'], 'question': manifest['question'],
              'workflow_state': 'draft', 'outcome': 'unresolved', 'sources': record_sources,
              'claims': [], 'evidence': [], 'reviews': [],
              'activities': [{'id': 'capture-' + operation_sha256[:32],
                              'description': 'Captured explicitly selected local artifact bytes; no claims inferred.',
                              'actor_as_recorded': 'prim-library-local-capture', 'at': captured_at}],
              'ingestion': {'operation_id': manifest['operation_id'], 'operation_sha256': operation_sha256,
                            'receipt': 'ingestion-receipt.json', 'extensions': manifest.get('extensions', {})}}
    temp = Path(tempfile.mkdtemp(prefix='.prim-capture-', dir=output.parent))
    pack = temp / 'pack'
    try:
        create(library, PROFILE, version, pack, values)
        # Keep all private capture metadata and originals private on POSIX.
        for path in pack.iterdir():
            path.chmod(0o600)
        (pack / 'artifacts').mkdir(mode=0o700)
        for sha, raw in blobs.items():
            write_new(pack / 'artifacts' / (sha+'.bin'), raw)
        files = inventory(pack, blobs)
        receipt = {'format': 'prim-ingestion-receipt', 'version': 1, 'operation_sha256': operation_sha256,
                   'request': request, 'profile': profile, 'captured_at': captured_at, 'sources': sources,
                   'inventory': files, 'inventory_sha256': fingerprint(files),
                   'checks': CHECKS}
        raw_receipt = canonical(receipt) + b'\n'
        if len(raw_receipt) > MAX_DOCUMENT:
            raise LibraryError('capture receipt exceeds its byte budget')
        write_new(pack / 'ingestion-receipt.json', raw_receipt)
        if output.exists() or output.is_symlink():
            raise LibraryError('capture destination appeared during creation')
        pack.rename(output)
    finally:
        shutil.rmtree(temp)
    return {'status': 'captured', 'path': str(output), 'operation_sha256': operation_sha256,
            'receipt_sha256': hashlib.sha256(raw_receipt).hexdigest(), 'sources': len(sources),
            'unique_artifacts': len(blobs), 'claims_created': 0, 'authorization': 'recorded_not_verified'}
