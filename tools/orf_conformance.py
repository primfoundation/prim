#!/usr/bin/env python3
"""Run the unchanged pinned ORF CLI, then compare byte-preserved inspections."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import research
from research_store import canonical, load_transport, preserve, read_directory, restore


def run() -> dict:
    lock = research.verify_baseline()
    upstream = research.BASELINE / 'upstream'
    commands = [
        (['--selftest'], 0),
        (['examples/orf-minimal'], 0),
        (['--strict', 'examples/orf-minimal'], 0),
        (['examples/orf-bad-done-without-go'], 1),
        (['--strict', 'examples/orf-bad-done-without-go'], 1),
    ]
    checks = []
    for args, expected in commands:
        proc = subprocess.run([sys.executable, '-B', '-m', 'orf.validate', *args],
                              cwd=upstream, capture_output=True, text=True, timeout=20)
        checks.append({'command': ['python', '-B', '-m', 'orf.validate', *args],
                       'expected_exit': expected, 'actual_exit': proc.returncode,
                       'passed': proc.returncode == expected,
                       'stdout': proc.stdout.replace(str(upstream), '$UPSTREAM'), 'stderr': proc.stderr})
    roundtrips = []
    for name in ['orf-minimal', 'orf-bad-done-without-go']:
        files, dirs = read_directory(upstream / 'examples' / name)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'preserved.json').write_bytes(canonical(preserve(files, dirs)))
            loaded, loaded_dirs = load_transport(root / 'preserved.json')
            restore(loaded, loaded_dirs, root / 'restored')
            same_bytes = read_directory(root / 'restored') == (files, dirs)
            for strict in [False, True]:
                before = research.inspect(files, dirs, strict=strict)
                after = research.inspect(loaded, loaded_dirs, strict=strict)
                roundtrips.append({'fixture': name, 'strict': strict, 'bytes_equal': same_bytes,
                                   'inspection_equal': before == after, 'legacy_status': before['legacy_validation']['status']})
    return {'recorded_at': datetime.now(timezone.utc).isoformat(),
            'scope': 'Pinned ORF CLI and preservation transport; not Research vNext migration or source verification',
            'source_commit': lock['commit'], 'source_tree': lock['tree'], 'files_checked': len(lock['files']),
            'success': all(c['passed'] for c in checks) and all(r['bytes_equal'] and r['inspection_equal'] for r in roundtrips),
            'commands': checks, 'roundtrips': roundtrips,
            'not_established': ['factual correctness', 'source independence', 'authenticated authority',
                                'Research vNext semantic migration', 'independent implementation review']}


def main() -> int:
    try:
        report = run()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report['success'] else 1
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f'Conformance run failed: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
