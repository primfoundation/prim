"""Behavioral distribution tests over synthetic external sources and real files."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from prim_library.cli import create, main
from prim_library.library import Library, LibraryError, canonical, fingerprint
from prim_library.publishing import publish, compile_library, read_local
from prim_library.resolution import (DEPENDENCIES, check_source, resolve_data,
                                     resolve_file, restore, MAX_SOURCE)


def definition(profile_id='outside/note', version='1.0.0', maturity='stable', requires=None):
    metadata = {'id': profile_id, 'name': 'External note', 'description': 'Synthetic external definition.',
                'version': version, 'maturity': maturity, 'kinds': ['note']}
    if requires is not None:
        metadata['extensions'] = {DEPENDENCIES: {'version': 1, 'requires': requires}}
    entry = {'metadata': metadata, 'resources': {}}
    entry['definition_sha256'] = fingerprint(entry)
    return entry


def source(entries, withdrawn=None):
    snapshot = {'format': 'prim-library', 'version': 1, 'definitions': entries,
                'snapshot_sha256': fingerprint(entries)}
    return canonical({'format': 'prim-library-source', 'version': 1, 'library': snapshot,
                      'withdrawn': withdrawn or []}) + b'\n'


def pin(entry):
    return {'id': entry['metadata']['id'], 'version': entry['metadata']['version'],
            'definition_sha256': entry['definition_sha256']}


def request(raws, requirements=None):
    return {'format': 'prim-library-request', 'version': 1, 'allow_deprecated': False,
            'sources': [{'name': f'source-{i}', 'sha256': hashlib.sha256(raw).hexdigest(),
                         'visibility': 'private', 'namespaces': ['outside']} for i, raw in enumerate(raws)],
            'requirements': requirements or [{'id': 'outside/note', 'version': '1.0.0'}]}


def solve(raws, requirements=None, **changes):
    req = request(raws, requirements)
    req.update(changes)
    return resolve_data(req, {hashlib.sha256(raw).hexdigest(): raw for raw in raws})


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_external_publisher_builds_creates_and_restores_without_original_source(self):
        package = self.root / 'publisher'
        package.mkdir()
        (package / 'PROFILE.md').write_text('''---
format: prim-profile
manifest_version: '0.1'
id: outside/note
name: External note
description: Synthetic publisher authored outside the Foundation checkout.
version: 1.0.0
maturity: development
kinds: [note]
resources:
  creation: creation.json
  schema: schema.json
  template: template.json
  examples: examples
---
A minimal external note definition. This body is data, never host instructions.
''')
        (package / 'examples').mkdir()
        (package / 'examples' / 'private.json').write_text('{"do-not-distribute":true}')
        (package / 'ignored.py').write_text('raise RuntimeError("must not execute")')
        (package / 'schema.json').write_text(json.dumps({'type': 'object', 'required': ['id', 'title'],
                'properties': {'id': {'type': 'string'}, 'title': {'type': 'string'}}}))
        (package / 'template.json').write_text('{"id":"", "title":"Untitled external note"}')
        (package / 'creation.json').write_text(json.dumps({'schema_resource': 'schema',
                'template_resource': 'template', 'authority_file': 'note.json', 'rules': {},
                'identity_field': 'id', 'title_field': 'title', 'privacy': 'local', 'scope': 'synthetic test'}))
        exported = self.root / 'publisher.json'
        publication = publish(package, exported)
        raw = exported.read_bytes()
        self.assertEqual(publication['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertNotIn(b'do-not-distribute', raw)
        self.assertNotIn(b'must not execute', raw)
        req = request([raw])
        req['sources'][0]['path'] = exported.name
        request_path = self.root / 'request.json'
        request_path.write_bytes(canonical(req))
        output = self.root / 'resolved'
        result = resolve_file(request_path, output)
        lock_path = output / 'prim-library.lock.json'
        self.assertNotIn(str(self.root), lock_path.read_text())
        self.assertNotIn('path', json.loads(lock_path.read_text())['request']['sources'][0])
        exported.unlink()
        moved_cache = self.root / 'moved-cache'
        (output / 'sources').rename(moved_cache)
        replay = self.root / 'restored'
        restored = restore(lock_path, moved_cache, replay, result['lock_sha256'])
        self.assertEqual(restored['snapshot_sha256'], result['snapshot_sha256'])
        self.assertEqual((output / 'library.json').read_bytes(), (replay / 'library.json').read_bytes())
        library = Library(json.loads((replay / 'library.json').read_text()))
        created = create(library, 'outside/note', '1.0.0', self.root / 'private-note',
                         {'unknown_extension': {'preserved': True}})
        self.assertEqual(created['validation']['status'], 'passed')
        self.assertTrue(json.loads((self.root / 'private-note/note.json').read_text())['unknown_extension']['preserved'])
        if os.name == 'posix':
            self.assertEqual(replay.stat().st_mode & 0o777, 0o700)
            self.assertEqual((replay / 'library.json').stat().st_mode & 0o777, 0o600)
        with self.assertRaises(LibraryError):
            restore(lock_path, moved_cache, replay, result['lock_sha256'])

    def test_dependency_closure_and_diamond_share_exact_pin(self):
        common = definition('outside/common')
        left = definition('outside/left', requires=[pin(common)])
        right = definition('outside/right', requires=[pin(common)])
        root = definition(requires=[pin(left), pin(right)])
        lock, _ = solve([source([root, right, common, left])])
        self.assertEqual([p['id'] for p in lock['definitions']], ['outside/common', 'outside/left', 'outside/note', 'outside/right'])

    def test_conflicting_dependency_versions_fail(self):
        a, b = definition('outside/shared'), definition('outside/shared', '2.0.0')
        root = definition(requires=[pin(a)])
        with self.assertRaisesRegex(LibraryError, 'incompatible'):
            solve([source([a, b, root])], [pin(root), pin(b)])

    def test_dependency_cycle_fails(self):
        a = definition(requires=[{'id': 'outside/other', 'version': '1.0.0'}])
        b = definition('outside/other', requires=[{'id': 'outside/note', 'version': '1.0.0'}])
        with self.assertRaisesRegex(LibraryError, 'cycle'):
            solve([source([a, b])])

    def test_missing_dependency_or_wrong_digest_fails(self):
        absent = definition('outside/missing')
        for entries in [[definition(requires=[pin(absent)])],
                        [definition(requires=[{**pin(absent), 'definition_sha256': '0'*64}]), absent]]:
            with self.subTest(entries=entries), self.assertRaises(LibraryError):
                solve([source(entries)])

    def test_mirrors_keep_all_origins_and_reordering_is_deterministic(self):
        raw = source([definition()])
        req = request([raw, raw])
        blobs = {hashlib.sha256(raw).hexdigest(): raw}
        one, _ = resolve_data(req, blobs)
        req['sources'].reverse()
        two, _ = resolve_data(req, blobs)
        self.assertEqual(one, two)
        self.assertEqual(one['definitions'][0]['sources'], ['source-0', 'source-1'])

    def test_identity_version_collision_never_uses_source_precedence(self):
        first, second = definition(), definition(maturity='beta')
        for raws in [[source([first]), source([second])], [source([second]), source([first])]]:
            with self.assertRaisesRegex(LibraryError, 'conflicting bytes'):
                solve(raws)

    def test_bounded_range_selects_highest_and_prerelease_is_opt_in(self):
        req = {'id': 'outside/note', 'minimum': '1.0.0', 'before': '2.0.0', 'allow_prerelease': False}
        raw = source([definition(version=v) for v in ['1.0.0', '1.5.0', '1.9.0-rc.1', '2.0.0']])
        self.assertEqual(solve([raw], [req])[0]['definitions'][0]['version'], '1.5.0')
        self.assertEqual(solve([raw], [{**req, 'allow_prerelease': True}])[0]['definitions'][0]['version'], '1.9.0-rc.1')

    def test_range_reuses_an_exact_dependency_pin(self):
        lower, higher = definition(), definition(version='1.5.0')
        root = definition('outside/root', requires=[pin(lower)])
        roots = [pin(root), {'id': 'outside/note', 'minimum': '1.0.0', 'before': '2.0.0', 'allow_prerelease': False}]
        lock, _ = solve([source([lower, higher, root])], roots)
        self.assertEqual(lock['definitions'][0]['version'], '1.0.0')

    def test_equal_precedence_builds_require_exact_version(self):
        raw = source([definition(version='1.0.0+a'), definition(version='1.0.0+b')])
        with self.assertRaisesRegex(LibraryError, 'equal-precedence'):
            solve([raw], [{'id': 'outside/note', 'minimum': '1.0.0', 'before': '2.0.0', 'allow_prerelease': False}])
        self.assertEqual(solve([raw], [{'id': 'outside/note', 'version': '1.0.0+b'}])[0]['definitions'][0]['version'], '1.0.0+b')

    def test_deprecated_requires_explicit_policy_and_retains_warning(self):
        raw = source([definition(maturity='deprecated')])
        with self.assertRaises(LibraryError):
            solve([raw])
        lock, _ = solve([raw], allow_deprecated=True)
        self.assertEqual(lock['definitions'][0]['maturity'], 'deprecated')

    def test_withdrawal_wins_over_unwithdrawn_mirror(self):
        entry = definition()
        plain = source([entry])
        withdrawn = source([entry], [{**pin(entry), 'reason': 'Synthetic withdrawal'}])
        for raws in [[plain, withdrawn], [withdrawn, plain]]:
            with self.assertRaises(LibraryError):
                solve(raws, allow_deprecated=True)
        # An explicitly retained older source remains reproducible; offline
        # history cannot discover a subsequent withdrawal automatically.
        self.assertEqual(len(solve([plain])[0]['definitions']), 1)

    def test_source_digest_snapshot_digest_and_resource_integrity_fail_closed(self):
        raw = source([definition()])
        with self.assertRaises(LibraryError):
            resolve_data(request([raw]), {hashlib.sha256(raw).hexdigest(): raw + b' '})
        broken = json.loads(raw)
        broken['library']['definitions'][0]['metadata']['name'] = 'forged'
        with self.assertRaises(LibraryError):
            solve([canonical(broken)])
        entry = definition()
        entry['resources'] = {'schema': {'text': '{}', 'sha256': '0'*64}}
        entry['definition_sha256'] = fingerprint({k: v for k, v in entry.items() if k != 'definition_sha256'})
        with self.assertRaises(LibraryError):
            solve([source([entry])])

    def test_withdrawal_tombstone_rejects_same_version_republication(self):
        original, replacement = definition(), definition(maturity='beta')
        with self.assertRaisesRegex(LibraryError, 'republished'):
            solve([source([replacement], [{**pin(original), 'reason': 'Withdrawn before source moved'}])])

    def test_out_of_scope_namespace_and_withdrawal_rejected(self):
        with self.assertRaisesRegex(LibraryError, 'namespaces'):
            solve([source([definition('imposter/note')])])
        with self.assertRaisesRegex(LibraryError, 'namespaces'):
            solve([source([definition()], [{**pin(definition('imposter/note')), 'reason': 'test'}])])

    def test_unknown_request_fields_aliases_and_duplicate_roots_rejected(self):
        raw = source([definition()])
        for change in [{'execute': 'script.py'}, {'requirements': [{'id': 'note', 'version': '1.0.0'}]},
                       {'requirements': [pin(definition()), pin(definition())]}, {'allow_deprecated': 1}]:
            with self.subTest(change=change), self.assertRaises(LibraryError):
                solve([raw], **change)

    def test_malformed_source_shapes_return_library_error(self):
        original = json.loads(source([definition()]))
        cases = [[], {}, {**original, 'version': True}, {**original, 'library': []}]
        for key, value in [('metadata', []), ('resources', []), ('metadata', {'id': []})]:
            candidate = deepcopy(original)
            candidate['library']['definitions'][0][key] = value
            cases.append(candidate)
        for candidate in cases:
            with self.subTest(candidate=candidate), self.assertRaises(LibraryError):
                check_source(canonical(candidate))
        for raw in [b'{"version":1,"version":1}', b'{"value":NaN}', b'['*30+b'0'+b']'*30, b' '* (MAX_SOURCE+1)]:
            with self.assertRaises(LibraryError):
                check_source(raw)

    def test_cache_miss_tampered_lock_and_cache_cannot_make_partial_bundle(self):
        raw = source([definition()])
        req = request([raw]); req['sources'][0]['path'] = 'source.json'
        (self.root / 'source.json').write_bytes(raw)
        request_path = self.root / 'request.json'; request_path.write_bytes(canonical(req))
        bundle = self.root / 'bundle'; result = resolve_file(request_path, bundle)
        lock_path = bundle / 'prim-library.lock.json'
        target = self.root / 'restore'
        with self.assertRaisesRegex(LibraryError, 'lock digest'):
            restore(lock_path, bundle/'sources', target, '0'*64)
        lock = json.loads(lock_path.read_bytes()); lock['definitions'][0]['version'] = '9.0.0'
        altered = canonical(lock); other = self.root / 'altered.json'; other.write_bytes(altered)
        with self.assertRaisesRegex(LibraryError, 'does not reproduce'):
            restore(other, bundle/'sources', target, hashlib.sha256(altered).hexdigest())
        cache_file = next((bundle/'sources').iterdir()); cache_file.write_bytes(raw+b' ')
        with self.assertRaisesRegex(LibraryError, 'corrupt'):
            restore(lock_path, bundle/'sources', target, result['lock_sha256'])
        cache_file.unlink()
        with self.assertRaises(OSError):
            restore(lock_path, bundle/'sources', target, result['lock_sha256'])
        self.assertFalse(target.exists())

    def test_symlink_and_fifo_inputs_do_not_follow_or_block(self):
        path = self.root / 'source'; path.write_bytes(b'{}')
        link = self.root / 'alias'; link.symlink_to(path)
        with self.assertRaises(LibraryError):
            read_local(link)
        directory = self.root / 'alias-dir'; directory.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(LibraryError):
            read_local(directory / 'source')
        if hasattr(os, 'mkfifo'):
            fifo = self.root / 'fifo'; os.mkfifo(fifo)
            with self.assertRaises(LibraryError):
                read_local(fifo)

    def test_dependency_and_aggregate_budgets(self):
        entries = [definition(f'outside/p{i}', requires=[{'id': f'outside/p{i+1}', 'version': '1.0.0'}]) for i in range(33)]
        entries.append(definition('outside/p33'))
        with self.assertRaisesRegex(LibraryError, 'depth'):
            solve([source(entries)], [{'id': 'outside/p0', 'version': '1.0.0'}])
        with self.assertRaises(LibraryError):
            solve([source([definition()])] * 17)


if __name__ == '__main__':
    unittest.main()
