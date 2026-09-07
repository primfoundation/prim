#!/usr/bin/env python3
"""Compile an explicitly selected local definition source. Never crawl or run profiles."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from profile_catalog import discover_profiles, _local_path, ProfileError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services/library/src'))
from prim_library.library import Library, fingerprint, MAX_DOCUMENT
from prim_library.popularity import POLICY

OUTPUT = ROOT / 'services/library/src/prim_library/data/library.json'
RANKINGS = ROOT / 'services/library/src/prim_library/data/rankings.json'


def compile_library(root: Path) -> dict:
    discovered = discover_profiles(root)
    definitions = []
    for entry in discovered['profiles']:
        folder = (root / entry['location']).parent.resolve()
        resources = {}
        # Only explicitly declared textual files are distributed, not directories,
        # user records, executable validators, or an entire repository.
        declared = {'manifest': 'PROFILE.md', **entry['metadata'].get('resources', {})}
        for name, rel in declared.items():
            p = _local_path(folder, rel)
            if p.is_dir():
                continue
            if p.suffix not in {'.md', '.json'} or p.stat().st_size > MAX_DOCUMENT:
                raise ProfileError('library resources must be bounded .md/.json files')
            raw = p.read_bytes()
            resources[name] = {'text': raw.decode('utf-8'), 'sha256': hashlib.sha256(raw).hexdigest()}
        item = {'metadata': entry['metadata'], 'resources': resources}
        item['definition_sha256'] = fingerprint(item)
        definitions.append(item)
    result = {'format': 'prim-library', 'version': 1, 'definitions': definitions,
              'snapshot_sha256': fingerprint(definitions)}
    Library(result, {'format': 'prim-popularity', 'version': 1, 'profiles': {}})
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=ROOT/'profiles')
    p.add_argument('--output', type=Path, default=OUTPUT)
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    full = compile_library(a.source.resolve())
    indexed = deepcopy(full)
    indexed["format"] = "prim-library-index"
    blobs = {}
    for entry in indexed["definitions"]:
        for resource in entry["resources"].values():
            text = resource.pop("text")
            blobs[resource["sha256"] + ".txt"] = text
    encoded = json.dumps(indexed, ensure_ascii=False, indent=2) + '\n'
    directory = a.output.parent / "resources"
    if a.check:
        if not a.output.exists() or a.output.read_text() != encoded:
            p.error('compiled library drift; run python tools/build_library.py')
        actual = {f.name for f in directory.iterdir() if f.is_file()} if directory.exists() else set()
        if actual != set(blobs) or any((directory / n).read_bytes() != text.encode("utf-8") for n, text in blobs.items()):
            p.error('compiled resource drift')
    else:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        directory.mkdir(exist_ok=True)
        for prior in directory.glob('*.txt'):
            if prior.name not in blobs:
                prior.unlink()
        for name, text in blobs.items():
            (directory / name).write_text(text, encoding='utf-8')
        a.output.write_text(encoded, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
