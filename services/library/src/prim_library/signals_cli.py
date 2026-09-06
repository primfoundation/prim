"""Offline operator entrypoint for consented, signed popularity signals. Never exposed by MCP."""
import argparse
import json
import os
from pathlib import Path
from .library import Library, LibraryError, load_json, canonical
from .popularity import Signals


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,required=True)
    sub=p.add_subparsers(dest='command',required=True)
    ingest=sub.add_parser('ingest');ingest.add_argument('input',type=Path)
    export=sub.add_parser('export');export.add_argument('--output',type=Path,required=True)
    forget=sub.add_parser('forget');forget.add_argument('issuer');forget.add_argument('subject')
    a=p.parse_args(argv)
    store=None
    try:
        # Secrets are environment-only; no key values appear in diagnostics or source.
        keys=json.loads(os.environ['PRIM_SIGNAL_ISSUERS_JSON'])
        if not isinstance(keys,dict) or any(not isinstance(v,str) for v in keys.values()):raise LibraryError('invalid issuer configuration')
        store=Signals(a.db,{k:v.encode() for k,v in keys.items()},os.environ['PRIM_SIGNAL_SUBJECT_SECRET'].encode())
        library = Library()
        ids = set()
        offset = 0
        while True:
            page = library.search(limit=50, offset=offset)
            ids.update(row['id'] for row in page['items'])
            if page['next_offset'] is None:
                break
            offset = page['next_offset']
        if a.command=='ingest':
            event=load_json(a.input.read_bytes(),4096)
            print(json.dumps({'status':store.ingest(event,ids)}))
        elif a.command=='forget':
            store.forget(a.issuer,a.subject);print('{"status":"forgotten"}')
        else:
            with a.output.open('xb') as stream:stream.write(canonical(store.export(ids))+b'\n')
            print('{"status":"exported"}')
        return 0
    except (KeyError,ValueError,OSError):
        print('Signal operation failed; check issuer configuration, signed consented event, or new output path.',file=__import__('sys').stderr)
        return 2
    finally:
        if store:store.close()


if __name__=='__main__':raise SystemExit(main())
