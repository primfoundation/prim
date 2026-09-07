"""Preserve the reviewed, sanitized source independently of generated snapshots."""
import hashlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class WorkbookMigrationTests(unittest.TestCase):
    def test_retained_legacy_sources_match_reviewed_upstream_blobs(self):
        expected = {
            'SPEC-0.1.0-draft.md': '2f5a66da6865b497379432c7f58c228d940787c9',
            'INTENTION.md': '50c6b3a416464226dccab523d477f36321280b23',
        }
        for name, source_blob in expected.items():
            with self.subTest(source=name):
                raw = (ROOT / 'profiles/workbook/legacy' / name).read_bytes()
                actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
                self.assertEqual(actual, source_blob, 'Retain source bytes; record interpretations separately.')


if __name__ == '__main__':
    unittest.main()
