"""Small accessible discovery view over the same catalog as MCP. No JavaScript."""
import html
from urllib.parse import quote


def page(results, query='', sort='relevance'):
    e=lambda x: html.escape(str(x),quote=True)
    cards=[]
    for row in results['items']:
        pop=row['popularity'];count=pop['metrics'].get('stars')
        detail=f"{count} stars" if count else 'No reportable popularity data'
        cards.append(f'''<article><h2>{e(row['name'])}</h2><p>{e(row['description'])}</p>
<p><code>{e(row['id'])}@{e(row['version'])}</code></p><p>{e(row['maturity'])} · {e(detail)}</p>
<details><summary>Definition and creation resources</summary><p>Digest: <code>{e(row['definition_sha256'])}</code></p>
<a href="/api/definitions/{quote(row['id'],safe='/')}/{quote(row['version'],safe='')}">Get the pinned definition</a>
<p>Available resources: {e(', '.join(row['resources']))}</p></details></article>''')
    options=''.join(f'<option value="{value}"'+(' selected' if sort==value else '')+f'>{label}</option>'
                    for value,label in [('relevance','Best match'),('popular','Popular'),('trending','Trending')])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prim Foundation Library</title><style>
:root{{color-scheme:light dark}}body{{font:17px/1.6 system-ui,sans-serif;margin:auto;padding:28px;max-width:880px}}
h1{{font-size:clamp(2rem,6vw,3.5rem);line-height:1.1}}h2{{font-size:1.3rem}}article{{padding:20px 0;border-top:1px solid}}
input,select,button{{font:inherit;padding:9px;max-width:100%;box-sizing:border-box}}form{{display:flex;gap:8px;flex-wrap:wrap;margin:32px 0}}
input{{flex:1;min-width:140px}}code{{font-size:.84em;overflow-wrap:anywhere}}.label{{font-size:.8rem;letter-spacing:.12em}}summary{{cursor:pointer}}
</style></head><body><header><p class="label">PRIM FOUNDATION · LIBRARY ALPHA</p><h1>Find the definition.<br>Keep the work.</h1>
<p>Open definitions that humans and agents can use to create portable Prims.</p></header>
<form method="get"><label for="q">Search</label><input id="q" name="q" value="{e(query)}" placeholder="Research, people, decisions…">
<label for="sort">Order</label><select id="sort" name="sort">{options}</select><button>Explore</button></form>
<p>{results['total']} definitions in this snapshot. Popularity is not security, quality, or truth.</p>
{''.join(cards) or '<p>No matching definition. Nothing has been silently substituted.</p>'}
<footer><h2>Connect your agent</h2><p>The MCP endpoint is <code>/mcp</code>. An installed server also works over stdio.</p>
<p>Search → pin a version and digest → get a creation kit → populate and validate locally.</p>
<p>No private Prim uploads, implicit voting, or hosted record validation. Development definitions are not ratified standards.</p>
<p>Snapshot: <code>{e(results['snapshot_sha256'])}</code></p></footer></body></html>'''
