#!/usr/bin/env python3
"""Run local checks and optionally the existing SDK; retain scoped evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-sdk", action="store_true", help="Also run the existing TypeScript SDK test command")
    parser.add_argument("--output", type=Path, default=ROOT / "tools/.verification/report.json")
    args = parser.parse_args()
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tools/tests", "-v"],
        [sys.executable, "tools/program.py", "check"],
        [sys.executable, "tools/program.py", "render", "--check"],
        [sys.executable, "tools/profile_catalog.py", "discover", "profiles", "--check", "registry/profiles.generated.json"],
        [sys.executable, "tools/profile_catalog.py", "inspect", "profiles/research"],
        [sys.executable, "-m", "compileall", "-q", "tools"],
    ]
    if args.with_sdk:
        commands.append(["npm", "--prefix", "sdk/typescript", "test"])
    checks = []
    for command in commands:
        display = ["python", *command[1:]] if command[0] == sys.executable else command
        try:
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
            record = {"command": display, "exit_code": result.returncode,
                      "stdout": result.stdout, "stderr": result.stderr}
        except (subprocess.TimeoutExpired, OSError) as exc:
            record = {"command": display, "exit_code": None, "stdout": "", "stderr": str(exc)}
        checks.append(record)
        print(f"{'PASS' if record['exit_code'] == 0 else 'FAIL'} {' '.join(display)}")
        if record["exit_code"] != 0:
            print(record["stdout"], end="")
            print(record["stderr"], end="", file=sys.stderr)
    paths = list((ROOT / "tools").rglob("*.py"))
    paths += [ROOT / "tools/requirements.txt", ROOT / "program/plan.json", ROOT / "ROADMAP.md", ROOT / "registry/profiles.generated.json"]
    paths += [p for p in (ROOT / "profiles/research").rglob("*") if p.is_file()]
    if args.with_sdk:
        paths += [p for p in (ROOT / "sdk/typescript").rglob("*") if p.is_file() and "node_modules" not in p.parts]
    inputs = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
    tests = re.search(r"Ran (\d+) tests", checks[0]["stderr"])
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10)
        commit = head.stdout.strip() if head.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        commit = None
    report = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Bootstrap checks plus existing TypeScript SDK command" if args.with_sdk else "Additive bootstrap checks only",
        "checkout_head": commit,
        "python": platform.python_version(), "platform": platform.system(),
        "dependencies": {"PyYAML": version("PyYAML")},
        "success": all(row["exit_code"] == 0 for row in checks),
        "unit_tests_run": int(tests.group(1)) if tests else None,
        "checks": checks, "input_sha256": inputs,
        "not_run": ([] if args.with_sdk else ["Existing TypeScript SDK regression"]) + [
            "ORF legacy validator/fixtures", "Desktop or browser UI", "Published-package installation",
            "Independent security review", "Real-account or production acceptance"],
        "limits": [
            "Commands and input hashes identify the tested scope, not an authenticated attestation.",
            "Publication, review, release and deployment are not inferred from tests or checkout HEAD.",
            "A manifest pass is not Research instance conformance, publisher verification, or security certification."],
    }
    if args.output.is_symlink():
        parser.error("report output must not be a symlink")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
