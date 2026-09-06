from __future__ import annotations

import base64
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import research
import research_store as store

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = research.BASELINE / 'upstream'
GOOD = UPSTREAM / 'examples/orf-minimal'
BAD = UPSTREAM / 'examples/orf-bad-done-without-go'


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        shutil.copytree(GOOD, self.source)
        (self.source / 'evidence').mkdir()
        (self.source / 'evidence/empty').mkdir()
        (self.source / 'evidence/opaque.bin').write_bytes(b'\x00\xff\r\n')
        (self.source / 'unknown.json').write_bytes(b'{"new_field":[1,2,3]}\r\n')
        self.files, self.dirs = store.read_directory(self.source)

    def bundle_file(self, value):
        path = self.root / 'bundle.json'
        path.write_text(json.dumps(value))
        return path

    def test_exact_roundtrip_preserves_unknown_binary_crlf_and_empty_directories(self):
        bundle = store.preserve(self.files, self.dirs)
        files, dirs = store.load_transport(self.bundle_file(bundle))
        target = self.root / 'restored'
        store.restore(files, dirs, target)
        self.assertEqual(store.read_directory(target), (self.files, self.dirs))
        self.assertEqual(store.read_directory(self.source), (self.files, self.dirs))

    def test_transport_is_deterministic(self):
        self.assertEqual(store.canonical(store.preserve(self.files, self.dirs)),
                         store.canonical(store.preserve(dict(reversed(list(self.files.items()))), list(reversed(self.dirs)))))

    def test_os_metadata_and_semantic_migration_limits_are_explicit(self):
        scope = ' '.join(store.preserve(self.files, self.dirs)['preservation_scope'])
        self.assertIn('executable bits', scope)
        self.assertIn('not semantic migration', scope)

    def test_modified_file_rejected(self):
        v = store.preserve(self.files, self.dirs)
        v['files'][0]['data_base64'] = base64.b64encode(b'changed').decode()
        with self.assertRaisesRegex(store.ResearchError, 'digest'):
            store.load_transport(self.bundle_file(v))

    def test_modified_payload_digest_rejected(self):
        v = store.preserve(self.files, self.dirs)
        v['payload_sha256'] = '0' * 64
        with self.assertRaisesRegex(store.ResearchError, 'digest'):
            store.load_transport(self.bundle_file(v))

    def test_duplicate_file_rejected(self):
        v = store.preserve(self.files, self.dirs)
        v['files'].append(v['files'][0])
        with self.assertRaisesRegex(store.ResearchError, 'duplicate'):
            store.load_transport(self.bundle_file(v))

    def test_duplicate_json_key_rejected(self):
        path = self.root / 'duplicate.json'
        path.write_text('{"format":1,"format":2}')
        with self.assertRaises(store.ResearchError):
            store.load_transport(path)

    def test_unknown_transport_field_rejected(self):
        v = store.preserve(self.files, self.dirs)
        v['execute'] = 'malicious.py'
        with self.assertRaises(store.ResearchError):
            store.load_transport(self.bundle_file(v))

    def test_bool_is_not_transport_version(self):
        v = store.preserve(self.files, self.dirs)
        v['version'] = True
        with self.assertRaises(store.ResearchError):
            store.load_transport(self.bundle_file(v))

    def test_invalid_base64_rejected(self):
        v = store.preserve(self.files, self.dirs)
        v['files'][0]['data_base64'] = '!!'
        with self.assertRaises(store.ResearchError):
            store.load_transport(self.bundle_file(v))

    def test_path_traversal_rejected_before_any_output(self):
        for path in ['../outside', '/outside', 'a/../outside', 'a\\outside', 'C:/x', './x', 'a//b']:
            with self.subTest(path=path), self.assertRaises(store.ResearchError):
                store.preserve({path: b'x'}, [])

    def test_nonportable_paths_rejected(self):
        for path in ['nul', 'CON.md', 'x.', 'x ', 'a\x00b', 'a\nb', 'AUX.txt', '.git/config', 'e\u0301.md']:
            with self.subTest(path=path), self.assertRaises(store.ResearchError):
                store.preserve({path: b'x'}, ['.git'] if path.startswith('.git') else [])

    def test_case_collision_rejected(self):
        with self.assertRaisesRegex(store.ResearchError, 'case'):
            store.preserve({'Claim.md': b'a', 'claim.md': b'b'}, [])

    def test_missing_parent_rejected(self):
        with self.assertRaisesRegex(store.ResearchError, 'parent'):
            store.preserve({'a/b': b'x'}, [])

    def test_file_directory_collision_rejected(self):
        with self.assertRaises(store.ResearchError):
            store.preserve({'a': b'x'}, ['a'])

    def test_symlink_file_rejected(self):
        (self.source / 'link').symlink_to(self.source / 'index.md')
        with self.assertRaises(store.ResearchError):
            store.read_directory(self.source)

    def test_symlink_root_rejected(self):
        link = self.root / 'link'
        link.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(store.ResearchError):
            store.read_directory(link)

    def test_symlink_parent_rejected(self):
        link = self.root / 'link'
        link.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(store.ResearchError):
            store.read_directory(link / 'evidence')

    def test_fifo_rejected_without_blocking(self):
        import os
        if not hasattr(os, 'mkfifo'):
            self.skipTest('FIFO unavailable')
        os.mkfifo(self.source / 'fifo')
        with self.assertRaises(store.ResearchError):
            store.read_directory(self.source)

    def test_entry_count_limit(self):
        with patch.object(store, 'MAX_ENTRIES', 1), self.assertRaises(store.ResearchError):
            store.read_directory(self.source)

    def test_file_byte_limit(self):
        with patch.object(store, 'MAX_FILE_BYTES', 2), self.assertRaises(store.ResearchError):
            store.read_directory(self.source)

    def test_total_byte_limit(self):
        with patch.object(store, 'MAX_TOTAL_BYTES', 8), self.assertRaises(store.ResearchError):
            store.read_directory(self.source)

    def test_path_depth_limit(self):
        with self.assertRaises(store.ResearchError):
            store.relative_path('/'.join(['a'] * (store.MAX_DEPTH + 1)))

    def test_json_size_limit(self):
        p = self.bundle_file(store.preserve(self.files, self.dirs))
        with patch.object(store, 'MAX_JSON_BYTES', 2), self.assertRaises(store.ResearchError):
            store.load_transport(p)

    def test_restore_cannot_overwrite_existing_directory(self):
        with self.assertRaises(store.ResearchError):
            store.restore(self.files, self.dirs, self.source)
        self.assertEqual(store.read_directory(self.source), (self.files, self.dirs))

    def test_output_file_cannot_be_overwritten(self):
        p = self.root / 'report'
        p.write_bytes(b'prior')
        with self.assertRaises(store.ResearchError):
            store.write_new_file(p, b'new')
        self.assertEqual(p.read_bytes(), b'prior')

    def test_declared_python_is_never_executed(self):
        marker = self.root / 'executed'
        (self.source / 'validator.py').write_text(f'from pathlib import Path\nPath({str(marker)!r}).touch()')
        files, dirs = store.read_directory(self.source)
        research.inspect(files, dirs)
        self.assertFalse(marker.exists())

    def test_cli_cannot_write_inside_source(self):
        before = store.read_directory(self.source)
        proc = subprocess.run([sys.executable, str(ROOT / 'tools/research.py'), 'preserve', str(self.source),
                               '--output', str(self.source / 'copy.json')], capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(store.read_directory(self.source), before)

    def test_cli_roundtrip_and_offline_render(self):
        cli = ROOT / 'tools/research.py'
        bundle, target, view = self.root / 'out.json', self.root / 'out', self.root / 'out.html'
        commands = [('preserve', self.source, bundle), ('restore', bundle, target), ('render', bundle, view)]
        for action, source, dest in commands:
            p = subprocess.run([sys.executable, str(cli), action, str(source), '--output', str(dest)], capture_output=True, text=True, timeout=20)
            self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(store.read_directory(target), (self.files, self.dirs))
        self.assertIn('Historical validator: passed', view.read_text())


class InterpretationTests(unittest.TestCase):
    def setUp(self):
        self.files, self.dirs = store.read_directory(GOOD)
        self.finding = next(p for p in self.files if p.startswith('findings/'))

    def edit_face(self, old, new):
        self.files['index.md'] = self.files['index.md'].replace(old.encode(), new.encode())

    def codes(self, report):
        return {w['code'] for w in report['review_warnings']}

    def test_pinned_oracle_integrity_and_selftest(self):
        self.assertEqual(research.verify_baseline()['commit'], research.COMMIT)
        self.assertEqual(research.oracle().selftest(), 0)

    def test_strict_positive_fixture(self):
        r = research.inspect(self.files, self.dirs, strict=True)
        self.assertEqual(r['legacy_validation']['status'], 'passed')
        self.assertEqual(r['checks']['research_vnext_conformance'], 'not_checked')
        self.assertEqual(r['checks']['factual_accuracy'], 'not_checked')
        self.assertEqual(r['checks']['authorization'], 'not_verified')
        self.assertEqual(r['review_warnings'], [])

    def test_original_negative_fixture(self):
        r = research.inspect(*store.read_directory(BAD))
        self.assertEqual(r['legacy_validation']['status'], 'failed')
        rules = {p['rule'] for item in r['legacy_validation']['reports'] for p in item['problems']}
        self.assertIn('done_needs_go', rules)

    def test_research_preview_is_derived_not_authoritative_or_confirming(self):
        r = research.inspect(self.files, self.dirs)
        preview = r['research_preview']
        self.assertFalse(preview['authoritative'])
        self.assertEqual(preview['derived_from_payload'], r['payload_sha256'])
        self.assertEqual(len(preview['claims']), 2)
        for claim in preview['claims']:
            self.assertIn(claim['origin']['path'], self.files)
            for citation in claim['citations']:
                self.assertEqual(citation['relation'], 'cites')
                self.assertFalse(citation['retrieved'])

    def test_original_and_restored_results_match(self):
        report = research.inspect(self.files, self.dirs, strict=True)
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            store.write_new_file(p / 'x.json', store.canonical(store.preserve(self.files, self.dirs)))
            copy = research.inspect(*store.load_transport(p / 'x.json'), strict=True)
        self.assertEqual(copy, report)

    def test_blank_finding_historical_pass_is_not_research_completeness(self):
        self.files[self.finding] = b'No frontmatter here.\n'
        r = research.inspect(self.files, self.dirs, strict=True)
        self.assertEqual(r['legacy_validation']['status'], 'passed')
        self.assertIn('metadata_unparsed', self.codes(r))
        self.assertIn('review_field_missing', self.codes(r))

    def test_missing_status_historical_pass_reported_with_warning(self):
        self.edit_face('status: done\n', '')
        r = research.inspect(self.files, self.dirs, strict=True)
        self.assertEqual(r['legacy_validation']['status'], 'passed')
        self.assertIn('review_field_missing', self.codes(r))

    def test_inline_comment_disagreement_retained(self):
        self.edit_face('status: done', 'status: done # imported')
        r = research.inspect(self.files, self.dirs)
        self.assertIn('parser_disagreement', self.codes(r))
        doc = next(d for d in r['documents'] if d['role'] == 'face')
        self.assertEqual(doc['legacy_metadata']['status'], 'done # imported')
        self.assertEqual(doc['yaml_metadata']['status'], 'done')
        self.assertEqual(r['legacy_validation']['status'], 'failed')

    def test_duplicate_yaml_key_not_silently_reinterpreted(self):
        self.edit_face('approval: go', 'approval: pending\napproval: go')
        r = research.inspect(self.files, self.dirs)
        self.assertEqual(r['legacy_validation']['status'], 'passed')
        self.assertIn('metadata_unparsed', self.codes(r))

    def test_scalar_verified_is_engine_error_not_success(self):
        self.edit_face('verified:\n', 'verified: malformed\n')
        r = research.inspect(self.files, self.dirs)
        self.assertEqual(r['legacy_validation']['status'], 'engine_error')

    def test_unknown_version_not_silently_validated(self):
        self.edit_face('orf_version: "0.2.0"', 'orf_version: "0.2.1"')
        r = research.inspect(self.files, self.dirs)
        self.assertEqual(r['legacy_validation']['status'], 'not_checked')

    def test_conflicting_profile_not_dispatched(self):
        self.edit_face('profile: orf', 'profile: research')
        self.assertEqual(research.inspect(self.files, self.dirs)['legacy_validation']['status'], 'not_checked')

    def test_opaque_evidence_retained_but_not_claimed_validated(self):
        self.files['opaque.bin'] = b'\x00\xff'
        r = research.inspect(self.files, self.dirs)
        self.assertIn('opaque.bin', r['not_covered_by_legacy_validator'])

    def test_oversize_markdown_preserved_but_not_parsed(self):
        with patch.object(research, 'MAX_MARKDOWN', 10):
            r = research.inspect(self.files, self.dirs)
        self.assertEqual(r['legacy_validation']['status'], 'not_checked')
        self.assertIn('markdown_limit', self.codes(r))

    def test_invalid_utf8_preserved_and_disclosed(self):
        self.files[self.finding] += b'\xff'
        r = research.inspect(self.files, self.dirs)
        self.assertIn('invalid_utf8', self.codes(r))

    def test_legacy_host_count_does_not_establish_independence(self):
        engine = research.oracle()
        self.assertEqual(engine.distinct_hosts(['https://a.example.com/x', 'https://b.example.com/y']), 2)
        r = research.inspect(self.files, self.dirs)
        self.assertEqual(r['checks']['source_independence'], 'not_checked')

    def test_empty_directory_does_not_report_valid_research(self):
        r = research.inspect({}, [])
        self.assertEqual(r['legacy_validation']['status'], 'not_checked')
        self.assertEqual(r['checks']['research_vnext_conformance'], 'not_checked')

    def test_historical_strict_file_warning_gap_is_characterized(self):
        engine = research.oracle()
        text = self.files[self.finding].decode()
        text = text.replace('evidence: REASONED', 'evidence: CONFIRMED')
        text = '\n'.join(line for line in text.split('\n') if not line.startswith('disconfirmation:'))
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'findings'
            p.mkdir()
            (p / 'claim.md').write_text(text)
            reports = engine.validate_path(p / 'claim.md', strict=True)
        self.assertIn('disconfirmation', {problem.rule for r in reports for problem in r.problems if problem.level == 'warn'})

    def test_safe_parser_rejects_dangerous_or_ambiguous_yaml(self):
        for header in ['x: !!python/object/apply:os.system [echo bad]', 'a: &x hi\nb: *x', 'x: 1\nx: 2', 'x: {<<: y}']:
            with self.subTest(header=header), self.assertRaises(store.ResearchError):
                research.modern_metadata('---\n' + header + '\n---\n')

    def test_safe_parser_bounds_nesting(self):
        with self.assertRaises(store.ResearchError):
            research.modern_metadata('---\nx: ' + '[' * 20 + 'x' + ']' * 20 + '\n---')

    def test_render_escapes_script_and_never_embeds_remote_assets(self):
        self.files[self.finding] += b'<script>alert(1)</script><img src="https://evil.invalid/x">'
        text = research.render(research.inspect(self.files, self.dirs))
        self.assertNotIn('<script>', text)
        self.assertNotIn('<img ', text)
        self.assertIn('&lt;script&gt;', text)
        self.assertIn("default-src 'none'", text)

    def test_cli_unknown_validator_is_nonzero(self):
        with tempfile.TemporaryDirectory() as t:
            self.edit_face('orf_version: "0.2.0"', 'orf_version: "9.9.9"')
            p = Path(t) / 'pack'
            store.restore(self.files, self.dirs, p)
            proc = subprocess.run([sys.executable, str(ROOT / 'tools/research.py'), 'inspect', str(p)], capture_output=True, text=True, timeout=20)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(json.loads(proc.stdout)['legacy_validation']['status'], 'not_checked')


if __name__ == '__main__':
    unittest.main()
