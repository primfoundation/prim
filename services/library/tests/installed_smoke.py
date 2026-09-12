"""Run with a clean wheel-installed Python, from OUTSIDE the source checkout."""
from __future__ import annotations

import asyncio
import json
import hashlib
import shutil
import subprocess
import os
from pathlib import Path
import sys
import tempfile

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from prim_library import __version__
from prim_library.cli import create
from prim_library.library import Library


async def main():
    import prim_library
    module_path = Path(prim_library.__file__).resolve()
    if 'site-packages' not in module_path.parts:
        raise AssertionError('smoke must use the wheel installed in site-packages')
    library = Library()
    outcomes = []
    with tempfile.TemporaryDirectory() as tmp:
        for index, row in enumerate(library.search()['items']):
            result = create(library, row['id'], row['version'], Path(tmp) / str(index))
            assert result['validation']['status'] == 'passed'
            pin = json.loads((Path(tmp) / str(index) / 'prim-definition.lock.json').read_text())
            assert pin['definition_sha256'] == row['definition_sha256']
            outcomes.append({'profile': row['id'], 'version': row['version'], 'created': True})
        # Exercise the real installed CLI against a new external definition
        # authored here, with no imports from repository tooling or fixtures.
        publisher = Path(tmp) / 'external-publisher'
        publisher.mkdir()
        (publisher / 'PROFILE.md').write_text("""---
format: prim-profile
manifest_version: '0.1'
id: example/note
name: Example note
description: Synthetic outside-publisher installation fixture.
version: 0.1.0-dev.1
maturity: development
kinds: [note]
resources:
  creation: creation.json
  schema: schema.json
  template: template.json
---
A synthetic note definition; no external publisher endorsement is claimed.
""")
        (publisher / 'schema.json').write_text(json.dumps({'type': 'object', 'required': ['id', 'title'],
            'properties': {'id': {'type': 'string'}, 'title': {'type': 'string'}}}))
        (publisher / 'template.json').write_text('{"id":"", "title":"External note"}')
        (publisher / 'creation.json').write_text(json.dumps({'schema_resource': 'schema',
            'template_resource': 'template', 'authority_file': 'note.json', 'rules': {},
            'identity_field': 'id', 'title_field': 'title', 'privacy': 'local', 'scope': 'synthetic test'}))
        executable = shutil.which('prim-library', path=str(Path(sys.executable).parent))
        assert executable, 'installed console entrypoint must exist'
        def cli(*args):
            result = subprocess.run([executable, *map(str, args)], cwd=tmp, capture_output=True, text=True, timeout=30)
            assert result.returncode == 0, result.stderr
            return json.loads(result.stdout)
        source_path = Path(tmp) / 'source.json'
        publication = cli('publish', publisher, '--output', source_path)
        assert publication['sha256'] == hashlib.sha256(source_path.read_bytes()).hexdigest()
        request_path = Path(tmp) / 'request.json'
        request_path.write_text(json.dumps({'format': 'prim-library-request', 'version': 1,
            'allow_deprecated': False,
            'sources': [{'name': 'example', 'path': 'source.json', 'sha256': publication['sha256'],
                         'namespaces': ['example'], 'visibility': 'private'}],
            'requirements': [{'id': 'example/note', 'version': '0.1.0-dev.1'}]}))
        bundle = Path(tmp) / 'resolved'
        resolution = cli('resolve', request_path, '--output', bundle)
        source_path.unlink()
        shutil.rmtree(publisher)
        restored = Path(tmp) / 'restored'
        replay = cli('restore', bundle / 'prim-library.lock.json', '--cache', bundle / 'sources',
                     '--expected-sha256', resolution['lock_sha256'], '--output', restored)
        assert replay['snapshot_sha256'] == resolution['snapshot_sha256']
        pack = Path(tmp) / 'external-note'
        cli('--library', restored / 'library.json', 'create', 'example/note', '--version', '0.1.0-dev.1', '--output', pack)
        assert cli('--library', restored / 'library.json', 'check-pack', pack)['status'] == 'passed'
        original = Path(tmp) / 'original.bin'
        original.write_bytes(b'Synthetic original evidence\r\n\x00\xff')
        capture_manifest = Path(tmp) / 'capture.json'
        capture_manifest.write_text(json.dumps({'format': 'prim-artifact-capture', 'version': 1,
            'operation_id': 'installed-capture', 'title': 'Installed capture proof', 'question': None,
            'sources': [{'id': 'source-1', 'path': 'original.bin', 'locator': 'urn:example:original',
                'sha256': hashlib.sha256(original.read_bytes()).hexdigest(), 'media_type': 'application/octet-stream',
                'observed_at': None, 'permissions': {'may_store': True, 'may_share': False,
                                                    'basis_as_recorded': 'Synthetic fixture owner grant'}}]}))
        captured = Path(tmp) / 'captured-research'
        capture_result = cli('capture-research', capture_manifest, '--version', '0.3.0-dev.3', '--output', captured)
        original.unlink()
        retried = cli('capture-research', capture_manifest, '--version', '0.3.0-dev.3', '--output', captured)
        assert retried['status'] == 'replayed' and retried['receipt_sha256'] == capture_result['receipt_sha256']
        capture_manifest.unlink()
        transferred = Path(tmp) / 'transferred-research'
        archive = Path(tmp) / 'captured-research.zip'
        transfer = cli('export-pack', captured, '--output', archive)
        shutil.rmtree(captured)
        assert cli('check-transfer', archive, '--expected-sha256', transfer['archive_sha256'])['integrity'] == 'passed'
        cli('import-pack', archive, '--output', transferred, '--expected-sha256', transfer['archive_sha256'])
        assert cli('check-capture', transferred, '--expected-sha256', capture_result['receipt_sha256'])['status'] == 'passed'
        assert cli('check-pack', transferred)['status'] == 'passed'
        capture_proof = {'original_binary_capture': 'passed', 'retry_after_source_removal': 'passed',
                         'complete_zip_transfer_without_source_or_manifest': 'passed', 'claims_created': 0}
        distribution = {'external_publish_resolve_restore_create_check': 'passed',
                        'original_source_removed_before_restore': True,
                        'snapshot_sha256': resolution['snapshot_sha256']}
        old = os.getcwd()
        try:
            os.chdir(tmp)
            for mode in ['auto', 'legacy']:
                transport = StdioServerParameters(command=sys.executable, args=['-m', 'prim_library.server'])
                async with Client(transport, mode=mode, read_timeout_seconds=15) as client:
                    found = await client.call_tool('prim_search', {'query': 'research'})
                    assert not found.is_error
                    row = found.structured_content['items'][0]
                    kit = await client.call_tool('prim_get_creation_kit', {
                        'profile_id': row['id'], 'version': row['version'],
                        'expected_sha256': row['definition_sha256']})
                    assert not kit.is_error and kit.structured_content['authority_file'] == 'research.json'
        finally:
            os.chdir(old)
    print(json.dumps({'success': True, 'version': __version__, 'installed_from_site_packages': True,
                      'snapshot_sha256': library.snapshot_id, 'profiles': outcomes,
                      'stdio_client_modes': ['auto', 'legacy'], 'distribution': distribution, 'capture': capture_proof,
                      'not_established': ['public deployment', 'all client UIs', 'independent security review']}))


if __name__ == '__main__':
    asyncio.run(main())
