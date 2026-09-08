#!/usr/bin/env python3
"""Verify selected legacy blobs and run only fixed, reviewed synthetic cases."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'compatibility' / 'incubators'
BASELINES = ('opf-1.0.0', 'album-0.1.0-draft', 'ocsf-0.1.0-draft',
             'scene-0.1.0-draft', 'video-0.1.0-draft')


def verify_blobs(name: str) -> dict:
    root = BASE / name
    lock = json.loads((root / 'baseline.json').read_text())
    paths = set()
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, 'w', compression=zipfile.ZIP_STORED) as archive:
        for row in lock['files']:
            path = Path(row['path'])
            if path.is_absolute() or '..' in path.parts or row['path'] in paths:
                raise ValueError(f'{name}: invalid or duplicate source path')
            paths.add(row['path'])
            source = root / 'upstream' / path
            if source.is_symlink() or not source.resolve().is_relative_to(root / 'upstream'):
                raise ValueError(f'{name}: source must stay within baseline')
            data = source.read_bytes()
            actual = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                      'git_blob': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}
            if any(row[key] != value for key, value in actual.items()):
                raise ValueError(f'{name}: changed upstream bytes: {path}')
            archive.writestr(row['path'], data)
    actual_paths = {p.relative_to(root / 'upstream').as_posix()
                    for p in (root / 'upstream').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if paths != actual_paths:
        raise ValueError(f'{name}: source inventory differs from pinned selection')
    with zipfile.ZipFile(io.BytesIO(payload.getvalue())) as archive:
        for path in paths:
            if archive.read(path) != (root / 'upstream' / path).read_bytes():
                raise ValueError(f'{name}: selected-file roundtrip changed bytes')
    return {'baseline': name, 'source_commit': lock['commit'], 'files_verified': len(paths),
            'selected_file_zip_roundtrip': True, 'status': lock['status']}


def command(label: str, args: list[str], cwd: Path, expected: int) -> dict:
    proc = subprocess.run([sys.executable, '-B', *args], cwd=cwd, capture_output=True,
                          text=True, timeout=20)
    def clean(text: str) -> str:
        return text.replace(str(ROOT), '$REPOSITORY').replace(str(cwd), '$CASE')
    return {'case': label, 'expected_exit': expected, 'actual_exit': proc.returncode,
            'passed': proc.returncode == expected,
            'stdout': clean(proc.stdout)[-6000:], 'stderr': clean(proc.stderr)[-6000:]}


def run() -> dict:
    baselines = [verify_blobs(name) for name in BASELINES]
    opf = BASE / BASELINES[0] / 'upstream'
    checks = [command('opf original six validator tests',
                      ['-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_validate.py', '-v'], opf, 0),
              command('opf selftest', ['-m', 'opf', '--selftest'], opf, 0),
              command('opf exact synthetic source fixture', ['-m', 'opf', 'examples/v1-product'], opf, 0)]
    album_cli = str(BASE / BASELINES[1] / 'upstream' / 'validate.py')
    record = {'format': 'prim.album', 'version': '0.1.0', 'album_id': 'album:fixture:conformance',
              'title': 'Synthetic conformance', 'tracks': [
                  {'n': 1, 'id': 'patch', 'title': 'Patch', 'duration': 8, 'bpm': 120,
                   'source': {'kind': 'patch', 'bars': 4}},
                  {'n': 2, 'id': 'file', 'title': 'File', 'duration': 1,
                   'source': {'kind': 'file', 'path': 'audio/fixture.bin'}},
                  {'n': 3, 'id': 'citation', 'title': 'Citation', 'duration': 1,
                   'source': {'kind': 'cite', 'album_id': 'album:fixture:other', 'track': 'track-1'}}],
              'duration': 10}
    # A small declarative mutation list keeps accepted and rejected meanings explicit.
    cases = [('album patch file and cite source fixture', [], 0, False),
             ('reject track numbering gap', [(['tracks', 1, 'n'], 4)], 1, False),
             ('reject duplicate track identity', [(['tracks', 1, 'id'], 'patch')], 1, False),
             ('reject player state in authority', [(['playing'], True)], 1, False),
             ('reject inconsistent patch timing', [(['tracks', 0, 'duration'], 7)], 1, False),
             ('reject absent file source', [(['tracks', 1, 'source', 'path'], 'audio/absent.bin')], 1, False),
             ('reject unknown source kind', [(['tracks', 2, 'source', 'kind'], 'unknown')], 1, False),
             ('reject incomplete cite', [(['tracks', 2, 'source', 'track'], '')], 1, False),
             ('reject inconsistent total', [(['duration'], 11)], 1, False),
             ('known gap: unsupported version accepted', [(['version'], 'unsupported')], 0, True),
             ('known gap: nonfinite duration accepted', [(['tracks', 0, 'duration'], float('nan'))], 0, True),
             ('known gap: boolean duration accepted', [(['tracks', 1, 'duration'], True)], 0, True),
             ('known gap: outside pack file accepted', [(['tracks', 1, 'source', 'path'], '../outside-fixture.bin')], 0, True)]
    with tempfile.TemporaryDirectory(prefix='prim-incubator-conformance-') as directory:
        workspace = Path(directory)
        root = workspace / 'pack'
        (root / 'audio').mkdir(parents=True)
        (root / 'audio' / 'fixture.bin').write_bytes(b'synthetic; not playable audio\n')
        (workspace / 'outside-fixture.bin').write_bytes(b'synthetic boundary probe\n')
        (root / 'index.md').write_text('---\nprofile: album\ntype: album\nalbum_version: "0.1.0"\nalbum_id: album:fixture:conformance\ntitle: Synthetic conformance\nstatus: draft\nalbum: album.json\n---\n')
        for label, changes, expected, known_gap in cases:
            value = copy.deepcopy(record)
            for path, replacement in changes:
                target = value
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = replacement
            (root / 'album.json').write_text(json.dumps(value) + '\n')
            result = command(label, [album_cli, str(root)], workspace, expected)
            result['known_unsafe_input_gap'] = known_gap
            checks.append(result)
    checks.extend(scene_video_cases())
    return {'observed_at': datetime.now(timezone.utc).isoformat(),
            'scope': 'Exact selected public blobs, fixed pinned legacy validators and synthetic fixtures only.',
            'baselines': baselines, 'checks': checks, 'success': all(c['passed'] for c in checks),
            'not_established': ['semantic migration', 'arbitrary untrusted pack safety',
                                'independent implementation or review', 'consumer acceptance',
                                'new Foundation profile publication', 'full-history preservation']}


def scene_video_cases() -> list[dict]:
    """Preserve legacy layout-dependent behavior using only pinned sibling code."""
    checks = []
    scene = {'format': 'prim.scene', 'version': '0.1.0', 'scene_id': 'scene:fixture:one',
             'title': 'Synthetic scene', 'duration': 2, 'fps': 24, 'size': [320, 240],
             'intent': 'Conformance fixture', 'camera': {'keys': [
                 {'t': 0, 'pos': [0, 0, 3], 'look': [0, 0, 0], 'fov': 45},
                 {'t': 2, 'pos': [0, 0, 3], 'look': [0, 0, 0], 'fov': 45}]},
             'objects': [{'id': 'one', 'kind': 'sphere', 'position': [0, 0, 0], 'keys': [
                 {'t': 0, 'position': [0, 0, 0]}, {'t': 2, 'position': [0, 1, 0]}]}]}
    video = {'format': 'prim.video', 'version': '0.1.0', 'video_id': 'video:fixture:one',
             'title': 'Synthetic video', 'duration': 2,
             'scenes': [{'n': 1, 'pack': 'scenes/one', 'cites': 'scene:fixture:one'}]}
    with tempfile.TemporaryDirectory(prefix='prim-scene-video-conformance-') as directory:
        workspace = Path(directory)
        for name in ('scene', 'video'):
            target = workspace / ('prim.' + name)
            target.mkdir()
            shutil.copyfile(BASE / (name + '-0.1.0-draft') / 'upstream' / 'validate.py', target / 'validate.py')
        root = workspace / 'pack'
        child = root / 'scenes' / 'one'
        child.mkdir(parents=True)
        (root / 'index.md').write_text('---\nprofile: video\ntype: video\n---\n')
        (child / 'index.md').write_text('---\nprofile: scene\ntype: scene\n---\n')
        def invoke(label: str, target: str, expected: int, known_gap: bool = False) -> None:
            result = command(label, [str(workspace / ('prim.' + target) / 'validate.py'),
                                     str(child if target == 'scene' else root)], workspace, expected)
            result['known_unsafe_input_gap'] = known_gap
            checks.append(result)
        def write(s: dict = scene, v: dict = video) -> None:
            (child / 'scene.json').write_text(json.dumps(s) + '\n')
            (root / 'video.json').write_text(json.dumps(v) + '\n')
        write()
        invoke('scene valid timed fixture', 'scene', 0)
        invoke('video valid composed scene with pinned sibling validator', 'video', 0)
        broken = copy.deepcopy(scene)
        broken['camera']['keys'][-1]['t'] = 1
        write(broken)
        invoke('scene rejects incomplete camera duration', 'scene', 1)
        invoke('video propagates pinned scene rejection', 'video', 1)
        # Move only our synthetic copy, never a repository or user dependency.
        sibling = workspace / 'prim.scene' / 'validate.py'
        sibling.rename(sibling.with_suffix('.disabled'))
        invoke('known gap: video accepts invalid scene without sibling validator', 'video', 0, True)
        sibling.with_suffix('.disabled').rename(sibling)
        broken = copy.deepcopy(scene)
        broken['objects'][0]['keys'][-1]['position'] = [0, 1]
        write(broken)
        invoke('scene rejects malformed object animation vector', 'scene', 1)
        write()
        (child / 'renderer.html').write_text('<script>window.__duration = 3</script>')
        invoke('scene renderer duration drift is a hard failure', 'scene', 1)
        (child / 'renderer.html').unlink()
        for label, field, value in [('video rejects citation mismatch', 'cites', 'scene:fixture:other'),
                                    ('video rejects escaping scene path', 'pack', '../../outside'),
                                    ('video rejects numbering gap', 'n', 2),
                                    ('video rejects copied scene authority', 'camera', {})]:
            broken_video = copy.deepcopy(video)
            broken_video['scenes'][0][field] = value
            write(v=broken_video)
            invoke(label, 'video', 1)
    return checks


if __name__ == '__main__':
    try:
        report = run()
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report['success'] else 1)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f'Incubator conformance failed: {exc}', file=sys.stderr)
        raise SystemExit(2)
