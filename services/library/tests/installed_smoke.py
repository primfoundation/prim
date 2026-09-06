"""Run with a clean wheel-installed Python, from OUTSIDE the source checkout."""
from __future__ import annotations

import asyncio
import json
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
                      'stdio_client_modes': ['auto', 'legacy'],
                      'not_established': ['public deployment', 'all client UIs', 'independent security review']}))


if __name__ == '__main__':
    asyncio.run(main())
