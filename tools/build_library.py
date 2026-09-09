#!/usr/bin/env python3
"""Compile an explicitly selected local definition source. Never crawl or run profiles."""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services/library/src'))

OUTPUT = ROOT / 'services/library/src/prim_library/data/library.json'
RANKINGS = ROOT / 'services/library/src/prim_library/data/rankings.json'


from prim_library.publishing import compile_library


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
