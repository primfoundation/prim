#!/usr/bin/env python3
"""Retain actual bounded library tests plus the inherited Foundation regression."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    env = {**os.environ, 'PYTHONPATH': str(ROOT/'services/library/src'), 'OTEL_SDK_DISABLED': 'true'}
    with tempfile.TemporaryDirectory() as tmp:
        inherited = Path(tmp)/'foundation.json'
        commands = [
            [sys.executable, '-m', 'unittest', 'discover', '-s', 'services/library/tests', '-v'],
            [sys.executable, 'tools/build_library.py', '--check'],
            [sys.executable, 'tools/build_host_catalog.py', '--check'],
            [sys.executable, 'tools/verify.py', '--with-sdk', '--output', str(inherited)],
        ]
        checks = []
        for command in commands:
            try:
                result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
                row = {'command': ['python', *command[1:]], 'exit_code': result.returncode,
                       'stdout': result.stdout, 'stderr': result.stderr}
            except (subprocess.TimeoutExpired, OSError) as exc:
                row = {'command': command, 'exit_code': None, 'stdout': '', 'stderr': str(exc)}
            checks.append(row)
            print(('PASS ' if row['exit_code'] == 0 else 'FAIL ') + ' '.join(row['command']))
            if row['exit_code'] != 0:
                print(row['stdout']);print(row['stderr'], file=sys.stderr)
        baseline = json.loads(inherited.read_text()) if inherited.exists() else None
    sources = []
    for directory in ['services/library', 'profiles']:
        sources += [f for f in (ROOT/directory).rglob('*') if f.is_file() and not
                    any(part in {'__pycache__','build','dist','.venv'} or part.endswith('.egg-info') for part in f.parts)]
    sources += [ROOT/f for f in ['tools/build_library.py','tools/verify_library.py','program/plan.json',
                                 'ROADMAP.md','registry/profiles.generated.json']]
    count = re.search(r'Ran (\d+) tests', checks[0]['stderr'])
    report = {'recorded_at': datetime.now(timezone.utc).isoformat(),
              'scope': 'Library unit/protocol tests and full inherited Foundation regression; not package installation or deployment',
              'success': all(x['exit_code'] == 0 for x in checks),
              'library_tests': int(count.group(1)) if count else None,
              'inherited_tests': baseline.get('unit_tests_run') if baseline else None,
              'dependencies': {key: version(key) for key in ['mcp','jsonschema','uvicorn','PyYAML']},
              'checks': checks, 'inherited_report': baseline,
              'input_sha256': {f.relative_to(ROOT).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(set(sources))},
              'not_established': ['public hosted endpoint', 'package index publication', 'authenticated public signal collection',
                                  'independent review', 'full Research lifecycle or ORF semantic migration', 'all Foundation requirements']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
