"""Local ingestion contract: real bytes, private receipts, quotas and safe retries."""
from copy import deepcopy
import hashlib
import io
import json
import os
import shutil
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from prim_library.ingestion import capture_research, check_capture, read_artifact, MAX_ARTIFACT
from prim_library.library import Library, LibraryError, canonical
from prim_library.pack import read_pack

VERSION = '0.3.0-dev.3'


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.library = Library()
        self.output = self.root / 'research'
        self.manifest_path = self.root / 'capture.json'
        self.raw = b'Original\r\nevidence\x00\xff\x00'
        self.source = self.root / 'evidence.bin'
        self.source.write_bytes(self.raw)
        self.manifest = {'format': 'prim-artifact-capture', 'version': 1, 'operation_id': 'capture-1',
                         'title': 'Source preservation test', 'question': 'What does this source establish?',
                         'sources': [self.row('source-1', self.source, self.raw)],
                         'extensions': {'unknown_property': {'keep': [1, 'two']}}}

    def row(self, identity, path, raw):
        return {'id': identity, 'path': path.name, 'locator': 'urn:example:source:' + identity,
                'sha256': hashlib.sha256(raw).hexdigest(), 'media_type': 'application/octet-stream',
                'observed_at': '2026-09-09T12:00:00+00:00',
                'permissions': {'may_store': True, 'may_share': False, 'basis_as_recorded': 'Synthetic fixture owner grant'},
                'extensions': {'source_note': 'Retain this metadata'}}

    def capture(self, manifest=None, output=None):
        self.manifest_path.write_bytes(canonical(self.manifest if manifest is None else manifest))
        return capture_research(self.library, VERSION, self.manifest_path, output or self.output)

    def test_original_binary_bytes_permissions_and_unknown_metadata_survive(self):
        result = self.capture()
        self.assertEqual(result['status'], 'captured')
        pack = read_pack(self.library, self.output)
        self.assertEqual(pack['validation']['status'], 'passed')
        record = pack['record']; source = record['sources'][0]
        self.assertEqual((self.output / source['artifact']['path']).read_bytes(), self.raw)
        self.assertEqual(source['permissions_as_recorded'], self.manifest['sources'][0]['permissions'])
        self.assertEqual(source['capture_extensions'], self.manifest['sources'][0]['extensions'])
        self.assertEqual(record['ingestion']['extensions'], self.manifest['extensions'])
        self.assertEqual(source['observed_at_as_recorded'], '2026-09-09T12:00:00+00:00')
        self.assertEqual(source['artifact']['mtime_ns_as_observed'], str(self.source.stat().st_mtime_ns))
        self.assertEqual(record['workflow_state'], 'draft')
        self.assertEqual(record['outcome'], 'unresolved')
        for key in ['claims', 'evidence', 'reviews']:
            self.assertEqual(record[key], [])
        receipt_bytes = (self.output / 'ingestion-receipt.json').read_bytes()
        self.assertEqual(hashlib.sha256(receipt_bytes).hexdigest(), result['receipt_sha256'])
        receipt = json.loads(receipt_bytes)
        self.assertNotIn('path', receipt['request']['sources'][0])
        self.assertNotIn(str(self.root), receipt_bytes.decode())
        self.assertEqual(receipt['checks']['authorization'], 'recorded_not_verified')
        if os.name == 'posix':
            self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)
            self.assertTrue(all(p.stat().st_mode & 0o777 == 0o600 for p in self.output.rglob('*') if p.is_file()))

    def test_complete_folder_transfer_checks_originals_without_source_or_manifest(self):
        result = self.capture()
        moved = self.root / 'transferred'
        shutil.copytree(self.output, moved)
        shutil.rmtree(self.output)
        self.source.unlink(); self.manifest_path.unlink()
        self.assertEqual(check_capture(self.library, moved, result['receipt_sha256'])['status'], 'passed')
        with self.assertRaisesRegex(LibraryError, 'receipt digest'):
            check_capture(self.library, moved, '0'*64)
        (moved / 'ingestion-receipt.json').write_text('{}')
        with self.assertRaises(LibraryError):
            check_capture(self.library, moved, hashlib.sha256(b'{}').hexdigest())

    def test_receipt_cannot_upgrade_recorded_permission_or_truth(self):
        result = self.capture()
        path = self.output / 'ingestion-receipt.json'
        receipt = json.loads(path.read_text())
        receipt['checks']['factual_accuracy'] = 'passed'
        raw = canonical(receipt); path.write_bytes(raw)
        with self.assertRaisesRegex(LibraryError, 'cannot assert'):
            check_capture(self.library, self.output, hashlib.sha256(raw).hexdigest())

    def test_concurrent_source_change_is_detected(self):
        original = os.fstat
        count = 0
        def changing(fd):
            nonlocal count
            count += 1
            if count == 2:
                self.source.write_bytes(b'changed size during capture')
            return original(fd)
        with patch('prim_library.ingestion.os.fstat', side_effect=changing):
            with self.assertRaisesRegex(LibraryError, 'changed during capture'):
                read_artifact(self.source, MAX_ARTIFACT)

    def test_actual_typescript_reader_accepts_captured_record_and_preserves_metadata(self):
        self.capture()
        root = Path(__file__).resolve().parents[3]
        script = """import { ProfileLibrary } from './sdk/typescript/src/profile-library.ts';
const result = new ProfileLibrary().readPack(process.argv[1]);
process.stdout.write(JSON.stringify(result.record));"""
        result = subprocess.run(['node', '--experimental-strip-types', '--input-type=module', '-e', script, str(self.output)],
                                cwd=root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), read_pack(self.library, self.output)['record'])
        self.assertIsInstance(json.loads(result.stdout)['sources'][0]['artifact']['mtime_ns_as_observed'], str)

    def test_nonportable_metadata_fails_without_losing_or_coercing_it(self):
        for extension in [{'huge': 2**60}, {'e\u0301': 'not silently normalized'}]:
            self.manifest['extensions'] = extension
            with self.assertRaises(LibraryError):
                self.capture()
            self.assertFalse(self.output.exists())

    def test_duplicate_content_is_one_blob_but_two_distinct_sources(self):
        other = self.root / 'copy.bin'; other.write_bytes(self.raw)
        self.manifest['sources'].append(self.row('source-2', other, self.raw))
        result = self.capture()
        self.assertEqual((result['sources'], result['unique_artifacts']), (2, 1))
        self.assertEqual(len(read_pack(self.library, self.output)['record']['sources']), 2)
        self.assertEqual(len(list((self.output / 'artifacts').iterdir())), 1)

    def test_retry_after_source_deletion_or_move_is_idempotent(self):
        first = self.capture()
        before = {p.relative_to(self.output): p.read_bytes() for p in self.output.rglob('*') if p.is_file()}
        self.source.unlink()
        self.manifest['sources'][0]['path'] = 'moved-or-offline/evidence.bin'
        second = self.capture()
        self.assertEqual(second['status'], 'replayed')
        self.assertEqual(first['operation_sha256'], second['operation_sha256'])
        self.assertEqual(first['receipt_sha256'], second['receipt_sha256'])
        self.assertEqual(before, {p.relative_to(self.output): p.read_bytes() for p in self.output.rglob('*') if p.is_file()})

    def test_same_operation_changed_content_or_metadata_cannot_overwrite(self):
        self.capture()
        before = (self.output / 'research.json').read_bytes()
        for change in ['title', 'content', 'permission']:
            m = deepcopy(self.manifest)
            if change == 'title': m['title'] = 'Changed title'
            elif change == 'content': m['sources'][0]['sha256'] = '0'*64
            else: m['sources'][0]['permissions']['may_share'] = True
            with self.subTest(change=change), self.assertRaisesRegex(LibraryError, 'conflict'):
                self.capture(m)
        self.assertEqual(before, (self.output / 'research.json').read_bytes())

    def test_retry_refuses_to_overwrite_later_research_edits(self):
        self.capture()
        p = self.output / 'research.json'; record = json.loads(p.read_bytes()); record['title'] = 'Later work'; p.write_bytes(canonical(record))
        with self.assertRaisesRegex(LibraryError, 'changed'):
            self.capture()
        self.assertEqual(json.loads(p.read_bytes())['title'], 'Later work')

    def test_corrupt_or_missing_captured_artifact_cannot_replay(self):
        self.capture()
        blob = next((self.output / 'artifacts').iterdir())
        blob.write_bytes(b'forged')
        with self.assertRaisesRegex(LibraryError, 'altered'):
            self.capture()
        blob.unlink()
        with self.assertRaises(OSError):
            self.capture()

    def test_permission_denial_bad_timestamps_and_unknown_protocol_fail_before_write(self):
        cases = []
        for value in [False, None, 1]:
            m = deepcopy(self.manifest); m['sources'][0]['permissions']['may_store'] = value; cases.append(m)
        for value in ['2026-09-09', 'not-a-time']:
            m = deepcopy(self.manifest); m['sources'][0]['observed_at'] = value; cases.append(m)
        m = deepcopy(self.manifest); m['execute'] = 'evil.py'; cases.append(m)
        m = deepcopy(self.manifest); m['version'] = True; cases.append(m)
        m = deepcopy(self.manifest); m['sources'][0]['path'] = 'https://example.test/evidence'; cases.append(m)
        m = deepcopy(self.manifest); m['sources'] *= 2; cases.append(m)
        for m in cases:
            with self.subTest(m=m), self.assertRaises(LibraryError):
                self.capture(m)
            self.assertFalse(self.output.exists())

    def test_unknown_observation_time_stays_unknown(self):
        self.manifest['sources'][0]['observed_at'] = None
        self.capture()
        row = read_pack(self.library, self.output)['record']['sources'][0]
        self.assertIsNone(row['observed_at_as_recorded'])
        self.assertIsNotNone(row['accessed_at'])

    def test_source_digest_mismatch_leaves_no_partial_output(self):
        self.source.write_bytes(b'changed since inspection')
        with self.assertRaisesRegex(LibraryError, 'digest mismatch'):
            self.capture()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob('.prim-capture-*')), [])

    def test_file_total_and_count_quotas_leave_no_partial_output(self):
        too_big = b'x' * (MAX_ARTIFACT + 1)
        self.source.write_bytes(too_big)
        self.manifest['sources'][0]['sha256'] = hashlib.sha256(too_big).hexdigest()
        with self.assertRaises(LibraryError):
            self.capture()
        raw = b'x' * MAX_ARTIFACT; self.source.write_bytes(raw)
        self.manifest['sources'] = [self.row(f's{i}', self.source, raw) for i in range(5)]
        with self.assertRaises(LibraryError):
            self.capture()
        self.manifest['sources'] = [self.row(f's{i}', self.source, raw) for i in range(129)]
        with self.assertRaises(LibraryError):
            self.capture()
        self.assertFalse(self.output.exists())

    def test_archives_and_executable_text_are_preserved_without_execution_or_expansion(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr('../../outside.txt', b'not extracted')
            z.writestr('nested.zip', b'not inspected')
        self.source.write_bytes(stream.getvalue())
        self.manifest['sources'][0] = self.row('archive', self.source, stream.getvalue())
        script = self.root / 'script.py'; script.write_text('raise RuntimeError("do not execute")')
        self.manifest['sources'].append(self.row('script', script, script.read_bytes()))
        # No HTTP, parsers or dynamic validator imports are used by this capture.
        self.capture()
        self.assertFalse((self.root / 'outside.txt').exists())
        self.assertEqual(len(list((self.output / 'artifacts').iterdir())), 2)
        receipt = json.loads((self.output / 'ingestion-receipt.json').read_text())
        self.assertEqual(receipt['checks']['recursive_expansion'], 'not_performed')

    def test_symlink_fifo_and_unmanaged_destination_rejected(self):
        link = self.root / 'link.bin'; link.symlink_to(self.source)
        self.manifest['sources'][0]['path'] = link.name
        with self.assertRaises(LibraryError):
            self.capture()
        if hasattr(os, 'mkfifo'):
            fifo = self.root / 'fifo'; os.mkfifo(fifo); self.manifest['sources'][0]['path'] = fifo.name
            with self.assertRaises(LibraryError):
                self.capture()
        self.output.mkdir()
        marker = self.output / 'keep.txt'; marker.write_text('existing work')
        with self.assertRaises(OSError):
            self.capture()
        self.assertEqual(marker.read_text(), 'existing work')

    def test_late_failure_cleans_up_staging_and_preserves_sources(self):
        with patch('prim_library.ingestion.write_new', side_effect=OSError('synthetic disk failure')):
            with self.assertRaises(OSError):
                self.capture()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob('.prim-capture-*')), [])
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_changed_source_can_be_captured_as_separate_revision_with_lineage(self):
        first = self.capture()
        self.source.write_bytes(b'a corrected original')
        self.manifest['operation_id'] = 'capture-2'
        self.manifest['sources'][0]['sha256'] = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.manifest['extensions']['supersedes_receipt_sha256_as_recorded'] = first['receipt_sha256']
        second_output = self.root / 'correction'
        second = self.capture(output=second_output)
        self.assertNotEqual(first['operation_sha256'], second['operation_sha256'])
        self.assertEqual(read_pack(self.library, second_output)['record']['ingestion']['extensions']['supersedes_receipt_sha256_as_recorded'], first['receipt_sha256'])
        old = read_pack(self.library, self.output)['record']['sources'][0]
        self.assertEqual((self.output / old['artifact']['path']).read_bytes(), self.raw)


if __name__ == '__main__':
    unittest.main()
