"""orf.validate — check documents and packs against ORF v0.2.0.

A format without a checker is a suggestion. Stdlib only (same approach as emf.validate):
small frontmatter subset parsed without PyYAML.

    python3 -m orf.validate <file-or-pack-dir>...
    python3 -m orf.validate --selftest
    python3 -m orf.validate --strict examples/orf-minimal
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import OKF_VERSION, ORF_VERSION

# OKF base types + ORF face type
OKF_TYPES = {
    "claim",
    "rule",
    "learning",
    "question",
    "evidence-pointer",
    "investigation",
    "Investigation",  # ORF preferred face
    "ResearchPacket",
}
EVIDENCE = {"CONFIRMED", "REASONED", "UNVERIFIED"}
STATUSES = {"intake", "planned", "running", "done"}
APPROVALS = {"pending", "go"}
TIER_RANK = {"human": 3, "job": 2, "agent": 1}

FACE_NAMES = {"index.md", "investigation.md", "research.md"}


@dataclass
class Problem:
    level: str  # error | warn
    rule: str
    detail: str


@dataclass
class Report:
    path: Path
    problems: list[Problem] = field(default_factory=list)

    @property
    def errors(self) -> list[Problem]:
        return [p for p in self.problems if p.level == "error"]


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse the small YAML subset ORF uses (maps + dashed lists; no PyYAML)."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    return _parse_yaml_block(text[3:end])


def _parse_yaml_block(block: str) -> dict[str, Any]:
    """Parse nested maps and dashed lists by looking ahead on empty values."""
    out: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, out)]
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        container = stack[-1][1]

        if line.startswith("- "):
            i += 1
            continue

        if ":" not in line:
            i += 1
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()

        if val == "":
            j = i + 1
            kind = "empty"
            while j < len(lines):
                if not lines[j].strip() or lines[j].lstrip().startswith("#"):
                    j += 1
                    continue
                ind2 = len(lines[j]) - len(lines[j].lstrip())
                if ind2 <= indent:
                    break
                s = lines[j].strip()
                kind = "list" if s.startswith("- ") else "map"
                break
            if kind == "list":
                items: list[str] = []
                j = i + 1
                while j < len(lines):
                    if not lines[j].strip() or lines[j].lstrip().startswith("#"):
                        j += 1
                        continue
                    ind2 = len(lines[j]) - len(lines[j].lstrip())
                    if ind2 <= indent:
                        break
                    s = lines[j].strip()
                    if s.startswith("- "):
                        items.append(s[2:].strip().strip("'\""))
                        j += 1
                    else:
                        break
                container[key] = items
                i = j
                continue
            if kind == "map":
                child: dict[str, Any] = {}
                container[key] = child
                stack.append((indent, child))
                i += 1
                continue
            container[key] = {}
            i += 1
            continue

        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            container[key] = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
        elif val.lower() in ("null", "~", "none"):
            container[key] = None
        else:
            container[key] = val.strip("'\"")
        i += 1
    return out


def coerce_sources(sources: Any) -> list[str]:
    if isinstance(sources, list):
        return [s for s in sources if isinstance(s, str)]
    if isinstance(sources, dict) and "__list__" in sources:
        return [s for s in sources["__list__"] if isinstance(s, str)]
    return []


def tier_of(by: str) -> str:
    return (by or "").split(":", 1)[0]


def distinct_hosts(sources: list[Any]) -> int:
    hosts: set[str] = set()
    for s in sources or []:
        if not isinstance(s, str):
            continue
        h = urlparse(s).hostname if "://" in s else None
        if not h:
            # bare URL without scheme
            h = urlparse("https://" + s).hostname if s else None
        if h:
            h = h.lower()
            if h.startswith("www."):
                h = h[4:]
            hosts.add(h)
    return len(hosts)


def validate_document(fm: dict[str, Any], *, role: str = "any") -> list[Problem]:
    """Validate one document's frontmatter. role: face | finding | any."""
    p: list[Problem] = []

    if not fm:
        if role == "face":
            p.append(Problem("error", "frontmatter", "pack face needs YAML frontmatter"))
        return p

    okf_version = str(fm.get("okf_version") or "")
    if okf_version != OKF_VERSION:
        p.append(
            Problem(
                "error",
                "okf_base",
                f"every ORF document must be a valid OKF v{OKF_VERSION} document "
                f"(okf_version={fm.get('okf_version')!r})",
            )
        )

    if "orf_version" not in fm:
        p.append(Problem("warn", "orf_version", "no orf_version — reads as plain OKF"))
    else:
        orf_version = str(fm.get("orf_version"))
        if not re.fullmatch(r"\d+\.\d+\.\d+", orf_version):
            p.append(
                Problem(
                    "error",
                    "orf_version_shape",
                    f"orf_version={orf_version!r} — expected X.Y.Z (for example {ORF_VERSION})",
                )
            )
        elif ".".join(orf_version.split(".")[:2]) != okf_version:
            p.append(
                Problem(
                    "error",
                    "version_alignment",
                    f"orf_version={orf_version!r} must start with okf_version={okf_version!r}",
                )
            )
        elif orf_version != ORF_VERSION:
            p.append(
                Problem(
                    "warn",
                    "orf_version",
                    f"document declares {orf_version}; this validator implements {ORF_VERSION}",
                )
            )

    typ = fm.get("type")
    if typ not in OKF_TYPES:
        p.append(Problem("error", "type", f"{typ!r} is not an OKF/ORF type"))

    # Agents must not author intent (EMF rule; ORF respects it)
    if typ == "intent":
        v = fm.get("verified") or {}
        if tier_of(v.get("by") or "") == "agent":
            p.append(
                Problem(
                    "error",
                    "intent_agent",
                    "type: intent authored by agent — use EMF human intent; agents never author intent",
                )
            )

    if fm.get("verdict") is not None:
        p.append(
            Problem(
                "warn",
                "verdict_wrong_profile",
                "capital verdict on ORF doc — use deedee for WATCH/PASS/COMMIT",
            )
        )

    v = fm.get("verified") or {}
    by = v.get("by") or ""
    tier = tier_of(by)
    if by and tier not in TIER_RANK:
        p.append(
            Problem(
                "error",
                "verified.by",
                f"by={by!r} — must start with human:, job: or agent:",
            )
        )
    if not (v.get("method") or "").strip() and role in ("face", "finding"):
        p.append(
            Problem(
                "warn",
                "method",
                "no method — OKF: verified without one is a feeling",
            )
        )

    # Face rules
    if role == "face" or (
        role == "any" and typ in ("Investigation", "investigation", "ResearchPacket")
    ):
        status = (fm.get("status") or "").strip()
        if status and status not in STATUSES:
            p.append(Problem("error", "status", f"status={status!r} not in {sorted(STATUSES)}"))
        approval = (fm.get("approval") or "").strip()
        if approval and approval not in APPROVALS:
            p.append(
                Problem("error", "approval", f"approval={approval!r} not in {sorted(APPROVALS)}")
            )
        question = (fm.get("question") or "").strip()
        if status in ("planned", "running", "done") and not question:
            p.append(
                Problem(
                    "error",
                    "question_required",
                    f"status={status} requires non-empty question",
                )
            )
        if status == "done" and approval != "go":
            p.append(
                Problem(
                    "error",
                    "done_needs_go",
                    "status: done requires approval: go — no durable finish without human go",
                )
            )
        if approval == "go" and not question:
            p.append(
                Problem(
                    "error",
                    "go_needs_question",
                    "approval: go requires non-empty question",
                )
            )
        if not (fm.get("title") or "").strip():
            p.append(Problem("error", "title", "pack face needs a title"))

    # Finding evidence grades
    ev = fm.get("evidence")
    if ev is not None or role == "finding":
        if ev is not None and str(ev).upper() not in EVIDENCE:
            p.append(
                Problem(
                    "error",
                    "evidence",
                    f"evidence={ev!r} — use CONFIRMED|REASONED|UNVERIFIED",
                )
            )
        sources = coerce_sources(fm.get("sources"))
        hosts = distinct_hosts(sources)
        if str(ev or "").upper() == "CONFIRMED" and hosts < 2:
            p.append(
                Problem(
                    "error",
                    "confirmed_hosts",
                    f"CONFIRMED with {hosts} independent host(s) — need ≥2; downgrade to REASONED",
                )
            )
        if str(ev or "").upper() == "CONFIRMED" and not (fm.get("disconfirmation") or "").strip():
            p.append(
                Problem(
                    "warn",
                    "disconfirmation",
                    "CONFIRMED without disconfirmation note",
                )
            )

    return p


def validate_pack(root: Path, *, strict: bool = False) -> list[Report]:
    """Validate an investigation pack directory."""
    reports: list[Report] = []
    root = root.resolve()
    if not root.is_dir():
        r = Report(root, [Problem("error", "pack", "not a directory")])
        return [r]

    face_path = None
    for name in ("index.md", "investigation.md"):
        cand = root / name
        if cand.is_file():
            face_path = cand
            break
    if face_path is None:
        reports.append(
            Report(
                root / "index.md",
                [Problem("error", "face_missing", "pack needs index.md (ORF face)")],
            )
        )
        return reports

    face_fm = parse_frontmatter(face_path.read_text(encoding="utf-8", errors="replace"))
    face_probs = validate_document(face_fm, role="face")
    if "orf_version" not in face_fm:
        face_probs.append(
            Problem("error", "orf_version", "pack face must set orf_version to claim ORF")
        )
    reports.append(Report(face_path, face_probs))

    log = root / "log.md"
    if not log.is_file():
        reports.append(
            Report(log, [Problem("warn", "log_missing", "OKF/ORF packs SHOULD include log.md")])
        )

    findings_dir = root / "findings"
    if findings_dir.is_dir():
        for f in sorted(findings_dir.glob("*.md")):
            fm = parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
            reports.append(Report(f, validate_document(fm, role="finding")))
    else:
        status = (face_fm.get("status") or "").strip()
        if status == "done":
            reports.append(
                Report(
                    findings_dir,
                    [
                        Problem(
                            "warn" if not strict else "error",
                            "findings_missing",
                            "status: done but no findings/ directory",
                        )
                    ],
                )
            )

    # Other markdown (skip log, skip emf/ which is EMF profile)
    for f in sorted(root.rglob("*.md")):
        if f.name == "log.md":
            continue
        if face_path and f.resolve() == face_path.resolve():
            continue
        if "findings" in f.parts and f.parent.name == "findings":
            continue
        if "emf" in f.parts:
            continue  # EMF validator owns these
        if f.name in ("plan.md", "brief.md"):
            fm = parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
            if fm:
                reports.append(Report(f, validate_document(fm, role="any")))

    if strict:
        for rep in reports:
            for prob in rep.problems:
                if prob.level == "warn":
                    prob.level = "error"

    return reports


def validate_path(path: Path, *, strict: bool = False) -> list[Report]:
    path = path.resolve()
    if path.is_dir():
        # pack if index.md or looks like investigation
        if (path / "index.md").is_file() or (path / "findings").is_dir():
            return validate_pack(path, strict=strict)
        # else all md files
        reports: list[Report] = []
        for f in sorted(path.rglob("*.md")):
            if f.name == "log.md":
                continue
            fm = parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
            reports.append(Report(f, validate_document(fm, role="any")))
        return reports
    if path.is_file():
        fm = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        role = "face" if path.name in FACE_NAMES else "finding" if "findings" in path.parts else "any"
        return [Report(path, validate_document(fm, role=role))]
    return [Report(path, [Problem("error", "path", "not found")])]


def selftest() -> int:
    def face(**kw: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "okf_version": OKF_VERSION,
            "orf_version": ORF_VERSION,
            "type": "Investigation",
            "title": "Test investigation",
            "question": "Is X true?",
            "status": "done",
            "approval": "go",
            "verified": {
                "by": "agent:squiddie",
                "at": "2026-08-03",
                "method": "test",
            },
        }
        base.update(kw)
        return base

    def finding(**kw: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "okf_version": OKF_VERSION,
            "orf_version": ORF_VERSION,
            "type": "claim",
            "title": "claim",
            "evidence": "REASONED",
            "sources": ["https://a.example.com/x", "https://b.example.com/y"],
            "disconfirmation": "searched for counterexamples",
            "verified": {"by": "agent:squiddie", "at": "2026-08-03", "method": "arm"},
        }
        base.update(kw)
        return base

    errs = lambda d, role="any": {p.rule for p in validate_document(d, role=role) if p.level == "error"}

    # done without go
    assert "done_needs_go" in errs(
        face(approval="pending"), role="face"
    ), errs(face(approval="pending"), role="face")

    # go without question
    assert "go_needs_question" in errs(face(question="", approval="go"), role="face")

    # planned needs question
    assert "question_required" in errs(
        face(status="planned", question="", approval="pending"), role="face"
    )

    # good face
    assert not errs(face(), role="face")

    # ORF version follows the OKF compatibility line
    assert "version_alignment" in errs(face(orf_version="0.1.9"), role="face")
    assert "orf_version_shape" in errs(face(orf_version="0.2"), role="face")
    assert not errs(face(orf_version="0.2.1"), role="face")

    # CONFIRMED needs 2 hosts
    assert "confirmed_hosts" in errs(
        finding(
            evidence="CONFIRMED",
            sources=["https://same.example.com/a", "https://www.same.example.com/b"],
        ),
        role="finding",
    )
    assert "confirmed_hosts" not in errs(
        finding(evidence="CONFIRMED"),
        role="finding",
    )

    # agent intent forbidden
    assert "intent_agent" in errs(
        {
            "okf_version": OKF_VERSION,
            "orf_version": ORF_VERSION,
            "type": "intent",
            "title": "nope",
            "verified": {"by": "agent:x", "at": "2026-08-03", "method": "m"},
        }
    )

    # host helper
    assert distinct_hosts(["https://www.snopes.com/a", "https://snopes.com/b"]) == 1
    assert distinct_hosts(["https://a.com/x", "https://b.com/y"]) == 2

    # frontmatter parse
    doc = parse_frontmatter(
        f'---\nokf_version: "{OKF_VERSION}"\norf_version: "{ORF_VERSION}"\ntype: Investigation\n'
        'title: "T"\nquestion: "Q?"\nstatus: done\napproval: go\n'
        "verified:\n  by: agent:squiddie\n  at: 2026-08-03\n  method: test\n"
        "---\n\nbody\n"
    )
    assert doc["orf_version"] == ORF_VERSION, doc
    assert doc["approval"] == "go", doc
    assert doc["verified"]["by"] == "agent:squiddie", doc

    print(
        "selftest OK — done/go gate, question gates, CONFIRMED hosts, "
        "version alignment, intent authorship, host independence, frontmatter parse"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="orf.validate", description=__doc__)
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as errors",
    )
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.paths:
        ap.error("give a file or pack directory")

    bad = 0
    n_docs = 0
    for path in args.paths:
        for rep in validate_path(path, strict=args.strict):
            n_docs += 1
            errors = rep.errors
            bad += bool(errors)
            mark = "FAIL" if errors else ("warn" if rep.problems else "ok  ")
            print(f"{mark}  {rep.path}")
            for x in rep.problems:
                print(f"        {x.level:<5} {x.rule}: {x.detail}")
    print(f"\n{n_docs} path(s), {bad} with errors")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
