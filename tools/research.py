#!/usr/bin/env python3
"""Inspect, preserve, restore and render legacy ORF without rewriting its meaning.

This is a reference compatibility reader, not a published Research schema/SDK.
All content is untrusted data. Only the pinned, reviewed local oracle may run.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

import yaml
from research_store import (ResearchError, canonical, digest, load_input, payload_id,
                            preserve, read_regular, restore, write_new_file, real_local)

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'profiles/research/compatibility/orf-0.2.0'
COMMIT = '4ae78ddaec19ebbc2c1e93f8289e9c6993af057d'
ORACLE_BLOB = '2699d9ef1fe94074bf75359de5550409d842f686'
MAX_MARKDOWN = 256 * 1024


def verify_baseline() -> dict[str, Any]:
    lock = json.loads((BASELINE / 'baseline.json').read_text())
    if lock['commit'] != COMMIT:
        raise ResearchError('legacy oracle commit changed; review is required')
    root = BASELINE / 'upstream'
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts}
    if actual != {r['path'] for r in lock['files']}:
        raise ResearchError('legacy source inventory mismatch')
    for row in lock['files']:
        raw = read_regular(root / row['path'], 1_000_000)
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if len(raw) != row['bytes'] or digest(raw) != row['sha256'] or blob != row['git_blob']:
            raise ResearchError('legacy source digest mismatch')
        if row['path'] == 'orf/validate.py' and blob != ORACLE_BLOB:
            raise ResearchError('unreviewed legacy oracle')
    return lock


def oracle() -> Any:
    verify_baseline()
    name = '_prim_pinned_orf'
    if name + '.validate' not in sys.modules:
        directory = BASELINE / 'upstream/orf'
        for key, path in [(name, directory / '__init__.py'), (name + '.validate', directory / 'validate.py')]:
            spec = importlib.util.spec_from_file_location(key, path)
            if spec is None or spec.loader is None:
                raise ResearchError('cannot load reviewed legacy oracle')
            module = importlib.util.module_from_spec(spec)
            sys.modules[key] = module
            spec.loader.exec_module(module)
    return sys.modules[name + '.validate']


class LiteralLoader(yaml.BaseLoader):
    """Safe comparison parser. Scalars stay strings to avoid date/type coercion."""


def _unique_mapping(loader: Any, node: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for k, v in node.value:
        key = loader.construct_object(k, deep=True)
        if not isinstance(key, str) or key == '<<' or key in result:
            raise ResearchError('duplicate, merged or non-string YAML key')
        result[key] = loader.construct_object(v, deep=True)
    return result


LiteralLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def modern_metadata(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        raise ResearchError('missing YAML frontmatter')
    try:
        end = lines.index('---', 1)
    except ValueError as exc:
        raise ResearchError('missing closing frontmatter delimiter') from exc
    block = '\n'.join(lines[1:end])
    depth = 0
    try:
        for count, event in enumerate(yaml.parse(block), 1):
            if count > 2048:
                raise ResearchError('YAML event limit exceeded')
            if getattr(event, 'anchor', None) or getattr(event, 'tag', None) or isinstance(event, yaml.AliasEvent):
                raise ResearchError('anchors, aliases and explicit YAML tags are unsupported')
            if isinstance(event, (yaml.SequenceStartEvent, yaml.MappingStartEvent)):
                depth += 1
                if depth > 16:
                    raise ResearchError('YAML nesting limit exceeded')
            if isinstance(event, (yaml.SequenceEndEvent, yaml.MappingEndEvent)):
                depth -= 1
        data = yaml.load(block, Loader=LiteralLoader)
    except yaml.YAMLError as exc:
        raise ResearchError('malformed YAML') from exc
    if not isinstance(data, dict):
        raise ResearchError('frontmatter must be a mapping')
    return data


def inspect(files: dict[str, bytes], dirs: list[str], *, strict: bool = False) -> dict[str, Any]:
    ident = payload_id(files, dirs)
    legacy = oracle()
    documents: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    face = next((n for n in ['index.md', 'investigation.md'] if n in files), None)
    for name, raw in sorted(files.items()):
        if not name.endswith('.md'):
            continue
        role = 'face' if name == face else 'finding' if name.startswith('findings/') and name.count('/') == 1 else 'other'
        doc: dict[str, Any] = {'path': name, 'sha256': digest(raw), 'role': role}
        documents.append(doc)
        if len(raw) > MAX_MARKDOWN:
            doc['interpretation'] = 'not_checked_size_limit'
            warnings.append({'path': name, 'code': 'markdown_limit', 'detail': 'Preserved, but too large for the legacy parser.'})
            continue
        # Matches universal-newline reading used by the historical validator.
        text = raw.decode('utf-8', errors='replace').replace('\r\n', '\n').replace('\r', '\n')
        doc['text'] = text
        doc['legacy_metadata'] = legacy.parse_frontmatter(text)
        if text.encode('utf-8') != raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n'):
            warnings.append({'path': name, 'code': 'invalid_utf8', 'detail': 'Display used replacement characters; original bytes remain intact.'})
        try:
            modern = modern_metadata(text)
            doc['yaml_metadata'] = modern
            doc['interpretation'] = 'agrees' if modern == doc['legacy_metadata'] else 'differs'
            if modern != doc['legacy_metadata']:
                warnings.append({'path': name, 'code': 'parser_disagreement', 'detail': 'Historical subset parser and safe YAML reader differ; no automatic semantic migration.'})
        except ResearchError as exc:
            doc['interpretation'] = 'unparsed'
            if role in {'face', 'finding'}:
                warnings.append({'path': name, 'code': 'metadata_unparsed', 'detail': str(exc)})
        fm = doc['legacy_metadata']
        required = ['title', 'status', 'verified'] if role == 'face' else ['type', 'evidence', 'verified'] if role == 'finding' else []
        for field in required:
            if not fm.get(field):
                warnings.append({'path': name, 'code': 'review_field_missing', 'detail': f'{field} is absent; a legacy pass must not imply completeness.'})
    face_doc = next((d for d in documents if d['role'] == 'face'), {})
    fm = face_doc.get('legacy_metadata', {})
    result: dict[str, Any] = {
        'format': 'prim-research-inspection', 'version': 1,
        'payload_sha256': ident,
        'origin': {'profile': fm.get('profile'), 'orf_version': fm.get('orf_version'), 'okf_version': fm.get('okf_version')},
        'inventory': [{'path': p, 'bytes': len(b), 'sha256': digest(b)} for p, b in sorted(files.items())],
        'directories': sorted(dirs),
        'documents': documents, 'review_warnings': warnings,
        'legacy_validation': {'status': 'not_checked', 'strict': strict, 'commit': COMMIT, 'entrypoint': 'validate_path(directory)', 'reports': []},
        'checks': {'byte_inventory': 'passed', 'research_vnext_conformance': 'not_checked',
                   'factual_accuracy': 'not_checked', 'source_independence': 'not_checked',
                   'reviewer_identity': 'not_verified', 'authorization': 'not_verified', 'source_retrieval': 'not_performed'},
        'interpretation_policy': 'Historical metadata is reported as authored, not endorsed. Citations do not establish support. No automatic semantic migration.',
    }
    check = result['legacy_validation']
    if fm.get('orf_version') != '0.2.0' or fm.get('okf_version') != '0.2' or fm.get('profile', 'orf') != 'orf':
        check['reason'] = 'Only ORF 0.2.0 / OKF 0.2 is selected; missing or conflicting declarations do not select another validator.'
    elif any(d.get('interpretation') == 'not_checked_size_limit' for d in documents):
        check['reason'] = 'At least one Markdown file exceeds the parser limit.'
    else:
        # Freeze input bytes first, then run only reviewed repo code on that snapshot.
        with tempfile.TemporaryDirectory(prefix='prim-orf-read-') as tmp:
            target = Path(tmp) / 'pack'
            restore(files, dirs, target)
            try:
                reports = legacy.validate_path(target, strict=strict)
                check['reports'] = [{'path': r.path.relative_to(target).as_posix(),
                                     'problems': [{'level': p.level, 'rule': p.rule, 'detail': p.detail} for p in r.problems]}
                                    for r in reports]
                check['status'] = 'failed' if any(r.errors for r in reports) else 'passed'
            except Exception as exc:
                check['status'] = 'engine_error'
                check['reason'] = f'Historical validator raised {type(exc).__name__}; not a successful check.'
    # A derived research-facing view, not a second authority or a new instance schema.
    claims = []
    for doc in documents:
        if doc['role'] != 'finding':
            continue
        fields = doc.get('legacy_metadata', {})
        claims.append({
            'origin': {'path': doc['path'], 'sha256': doc['sha256']},
            'title': fields.get('title'),
            'recorded_evidence_grade': fields.get('evidence'),
            'recorded_verification': fields.get('verified'),
            'citations': [{'locator': url, 'relation': 'cites', 'retrieved': False}
                          for url in legacy.coerce_sources(fields.get('sources'))],
            'interpretation': doc.get('interpretation', 'not_checked'),
        })
    result['research_preview'] = {
        'derived_from_payload': ident, 'authoritative': False,
        'question': fm.get('question'), 'brief_as_recorded': fm.get('brief'),
        'workflow_status_as_recorded': fm.get('status'),
        'approval_as_recorded': fm.get('approval'), 'claims': claims,
    }
    inspected_paths = {r['path'] for r in check['reports']}
    result['not_covered_by_legacy_validator'] = [p for p in sorted(files) if p not in inspected_paths]
    return result


def render(report: dict[str, Any]) -> str:
    """Offline, script-free review view. Render content as escaped text, not HTML."""
    esc = lambda value: html.escape(str(value), quote=True)
    face = next((d for d in report['documents'] if d['role'] == 'face'), {})
    fm = face.get('legacy_metadata', {})
    title = fm.get('title', 'Preserved research')
    sections = []
    for doc in report['documents']:
        sections.append(f'<details><summary>{esc(doc["path"])} · {esc(doc["role"])}</summary>'
                        f'<p>Interpretation: {esc(doc.get("interpretation", "not_checked"))}</p>'
                        f'<pre>{esc(doc.get("text", "Content preserved but not displayed."))}</pre></details>')
    warnings = ''.join(f'<li><strong>{esc(w["path"])} — {esc(w["code"])}</strong>: {esc(w["detail"])}</li>' for w in report['review_warnings'])
    findings = [d for d in report['documents'] if d['role'] == 'finding']
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer"><title>{esc(title)} — Research review</title>
<style>body{{font:17px/1.6 system-ui,sans-serif;max-width:850px;margin:auto;padding:28px}}h1{{line-height:1.15;font-size:2.2rem}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.6 ui-monospace,monospace}}details{{padding:12px 0;border-bottom:1px solid}}summary{{cursor:pointer;overflow-wrap:anywhere}}aside{{border:2px solid;padding:16px}}code{{overflow-wrap:anywhere}}h2{{margin-top:32px}}</style></head>
<body><header><p>PRIM · RESEARCH COMPATIBILITY REVIEW</p><h1>{esc(title)}</h1>
<p>{esc(fm.get('question', 'No governing question could be interpreted.'))}</p></header>
<aside><strong>Historical validator: {esc(report['legacy_validation']['status'])}</strong>
<p>This is not a truth, security, authorization, or Research vNext conformance certificate.
Source independence and reviewer identity have not been verified. Original labels are preserved, not endorsed.</p></aside>
<p>{len(findings)} finding documents · {len(report['inventory'])} preserved files</p>
<h2>Review warnings</h2><ul>{warnings or '<li>No parser warnings. That does not establish factual correctness or completeness.</li>'}</ul>
<h2>Original documents</h2>{''.join(sections)}
<h2>Historical check report</h2><pre>{esc(json.dumps(report['legacy_validation'], indent=2))}</pre>
<h2>Preservation fingerprint</h2><code>{esc(report['payload_sha256'])}</code>
<p>Derived offline view. The original file bytes remain the authority. No source URLs were fetched.</p></body></html>'''


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    for name in ['inspect', 'preserve', 'restore', 'render']:
        item = sub.add_parser(name)
        item.add_argument('input', type=Path)
        if name != 'inspect':
            item.add_argument('--output', type=Path, required=True)
        if name == 'inspect':
            item.add_argument('--strict', action='store_true')
    sub.add_parser('verify-baseline')
    args = ap.parse_args(argv)
    try:
        if args.command == 'verify-baseline':
            lock = verify_baseline()
            print(json.dumps({'commit': lock['commit'], 'files_checked': len(lock['files']), 'status': 'passed'}))
            return 0
        if args.command != 'inspect' and args.input.is_dir():
            try:
                real_local(args.output).relative_to(real_local(args.input))
            except ValueError:
                pass
            else:
                raise ResearchError('output must not be placed inside the source pack')
        files, dirs = load_input(args.input)
        if args.command == 'preserve':
            write_new_file(args.output, canonical(preserve(files, dirs)) + b'\n')
        elif args.command == 'restore':
            restore(files, dirs, args.output)
        elif args.command == 'render':
            write_new_file(args.output, render(inspect(files, dirs)).encode('utf-8'))
        else:
            report = inspect(files, dirs, strict=args.strict)
            print(json.dumps(report, ensure_ascii=True, indent=2))
            return {'passed': 0, 'failed': 1, 'engine_error': 2, 'not_checked': 2}[report['legacy_validation']['status']]
        return 0
    except (ResearchError, OSError) as exc:
        print(f'Research error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
