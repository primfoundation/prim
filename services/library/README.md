# Prim Foundation Library MCP

**Search the definition. Create the Prim. Keep the work.**

An installable MCP service over **stdio** or **Streamable HTTP**, using the official
MCP Python SDK 2.1.1. Both current (2026-07-28) and legacy (2025-11-25 handshake)
client modes are exercised in protocol tests. This is an alpha implementation,
not a claim that every client UI or Foundation acceptance gate is complete.

The same immutable public library powers MCP, a small human catalog, a JSON API,
and local creation/validation. There is no per-profile endpoint or application.
The initial snapshot contains development definitions for Research, Person, Decision and
Workbook. Other legacy profiles are NOT automatically advertised as supported.
A new publisher adds a definition package, not a Foundation repository.

## Install and run

From an inspected checkout of this branch:

```bash
python -m pip install -c services/library/constraints.txt ./services/library
prim-foundation-mcp
```

Or install the built `prim_foundation_mcp-0.1.0a4-py3-none-any.whl`. The wheel
includes the compiled definitions; it works away from the source repository.
There is not yet a PyPI publication. A versioned Git-source install is also
possible: `pip install 'git+https://github.com/primfoundation/prim.git@COMMIT#subdirectory=services/library'`
with a reviewed full commit hash replacing `COMMIT`. Never assume a mutable
branch or a `latest` label is an immutable supply-chain pin.

Generic local MCP-host configuration, after installation:

```json
{
  "mcpServers": {
    "prim-foundation": {"command": "prim-foundation-mcp", "args": []}
  }
}
```

Some hosts need an absolute executable path; use the installed entrypoint in
your chosen environment. This is not a claim that a specific vendor has
approved a one-click installation or listed this service in its directory.

## Agent workflow

1. `prim_search` finds definitions by purpose; filter by maturity as needed.
2. `prim_get_definition` returns the exact version, digest, resources and status.
3. `prim_get_resource` loads only the specification/schema text needed.
4. `prim_get_creation_kit` requires that version AND digest and returns the
   schema, blank template, authority filename and declarative reference rules.
5. Populate and validate **locally**, using your own tools or the local CLI.

The server does not run an LLM, perform research, fabricate citations or infer
human intent. Agents can use the definitions without being coupled to a model
vendor. Model output still needs validation and human judgment where appropriate.

All six public tools are read-only. Other tools: `prim_list_versions` and
`prim_rankings`. Resources: `prim://library/catalog` and
`prim://definitions/{namespace}/{name}/{version}/{resource}`.
The `create_a_prim` prompt explains the same portable workflow.

## Local creation and validation

```bash
prim-library search research
prim-library create primfoundation/research --version 0.3.0-dev.3 --output ./new-research
prim-library validate primfoundation/research --version 0.3.0-dev.3 ./new-research/research.json
```

Use `--input ./your-local-record.json` with `create` to supply fields. Unknown
JSON fields survive. A new local directory receives authoritative JSON, a human
`index.md`, a creation log, and a definition lock with ID/version/full digest.
Existing destinations are never overwritten. Blank research is a draft, not
completed or approved research. Reuse the same pinned definition when editing.

A structural pass checks required fields and declared identifiers/relationships.
It does not establish factual accuracy, source independence, reviewer identity
or permission. Native Research is explicitly experimental. Historical ORF uses
the separate pinned compatibility tool; automatic semantic migration is not
implemented by renaming an ORF file. See `profiles/research/NATIVE.md`.

## Independent publishing and offline installation

The installed CLI now supports `publish`, `resolve` and `restore`. A publisher
can build a data-only distribution from their own `PROFILE.md` directory.
Consumers combine explicitly scoped, digest-pinned sources into a new local
library and portable cache. Exact locks survive source moves, deletion and
rollback; version conflicts, withdrawn definitions and dependency cycles fail.
No source URLs are fetched and no profile code is run.

See [the complete workflow and contract](../../program/DEFINITION-DISTRIBUTION.md)
and [the synthetic external note example](examples/external-note/PROFILE.md).
Local publication is implemented; authenticated publisher identity, automatic
remote refresh, aliases/transfers and a real outside-author trial remain open.

## Capture original evidence into a Research draft

`capture-research` turns an explicit local file manifest into a new private
Research draft with byte-preserved artifacts and an ingestion receipt. It keeps
source identity, capture time and recorded permissions separate from claims.
Retries verify the prior capture without overwriting later edits. `check-capture`
checks a transferred complete folder against the retained receipt digest.

See [the capture workflow and limits](../../program/ARTIFACT-CAPTURE.md) and
[the runnable synthetic example](examples/research-capture/capture.json).
Archives captured as evidence remain opaque bytes. Use `export-pack`,
`check-transfer` and `import-pack` to move the complete folder through a verified
ZIP envelope, preserving attachments, receipts and unknown files. See the
[complete-pack contract](../../program/COMPLETE-PACK-TRANSFER.md) for commands,
limits and the distinction between byte integrity and source authentication.

## Run the remotely connectable service

Local HTTP test:

```bash
prim-foundation-mcp --transport http --host 127.0.0.1 --port 8000
```

MCP endpoint: `http://127.0.0.1:8000/mcp`. Human catalog: `/`.
JSON search: `/api/prims`; versioned definition: `/api/definitions/namespace/name/version`.
Discovery document: `/.well-known/prim-library.json`; health: `/healthz`.
These are routes on the running service, not a claim of a live public Foundation URL.

A production operator must configure TLS at the edge, an exact Host allowlist,
allowed browser Origins when needed, edge rate limits and monitoring:

```bash
export PRIM_ALLOWED_HOSTS='your-approved-domain.example'
prim-foundation-mcp --transport http --host 0.0.0.0 --port 8000
```

Wildcard host `*` and public binding without an explicit allowlist are rejected.
The SDK validates Host/Origin and limits MCP request bodies to 64 KiB. Local
in-process request caps and concurrency bounds supplement, not replace, edge
quotas. No OAuth is needed for public read-only definitions; authenticated
private libraries and public voting need a separately enforced security design.

Serving a custom `--library /local/snapshot.json` over HTTP additionally requires
`PRIM_PUBLIC_LIBRARY_APPROVED=true`. The operator is responsible for ensuring it
contains only intentionally public definitions. No recursive remote crawling.
Local stdio can use private definitions without publishing or sending them out.

## Popularity and trending

Popular: `2*ln(1+active_stars) + ln(1+distinct_adoptions_30d)`.
Trending: `ln(1+distinct_adoptions_7d) * min(4,(week+5)/(previous_week+5))`.
Search relevance filters first. Equal/no-data scores tie by profile ID.
Stars, adoption, maturity, verification and security remain separate dimensions.

The initial published snapshot contains **no fabricated usage or votes**.
The signed-signal ingestion engine is operator-only and is NOT an MCP tool.
Registered collector services, not arbitrary clients, sign consented events.
Replay IDs, per-identity daily adoption deduplication, reversible stars,
out-of-order protection, deletion and minimum cohorts prevent simple inflation.
A signature proves the registered issuer supplied the event, not that the issuer
is honest or that two credentials represent two people. Account verification,
issuer onboarding and abuse review remain prerequisites to activating collection.

Operator commands (with environment-only issuer and subject-HMAC keys):

```bash
prim-library-signals --db /private/signals.sqlite ingest signed-event.json
prim-library-signals --db /private/signals.sqlite export --output new-rankings.json
prim-library-signals --db /private/signals.sqlite forget issuer subject
prim-foundation-mcp --rankings new-rankings.json
```

`PRIM_SIGNAL_ISSUERS_JSON` maps approved collector IDs to secrets of at least
32 bytes. `PRIM_SIGNAL_SUBJECT_SECRET` supplies an independent subject HMAC key.
Neither belongs in a repository or client configuration. Do not issue collector
keys to end users. Subject pseudonyms are private; only thresholded aggregates
are exported. Per-metric counts below five are suppressed. This is not a complete
anonymity or anti-Sybil guarantee. No profile opens or searches count as votes.
The signing/consent/identity service itself is not deployed by this alpha.

## Build and verify

```bash
python -m pip install -c services/library/constraints.txt ./services/library
python tools/build_library.py --check
python -m unittest discover -s services/library/tests -v
python tools/verify.py --with-sdk
python -m build --no-isolation services/library
```

The builder reuses the existing safe `PROFILE.md` discovery code and packages
only explicitly declared bounded Markdown/JSON resources. Complete-definition
hashes include schemas/templates, not only the manifest. Generated data must
match its source. Use `python tools/build_library.py` after editing definitions.
Compiled data is a distribution view; `profiles/` remains the definition source.

## Sources informing the transport

- https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
- https://py.sdk.modelcontextprotocol.io/run/deploy/
- https://py.sdk.modelcontextprotocol.io/migration/
- https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.1.1

See `SECURITY.md` for explicit boundaries and `program/HANDOFF.md` for verified
release/deployment state. Independent security review, broad client testing,
package-index publication, public endpoint ownership and operations remain gates.
# Offline host export and pack checking

`prim-library export-host` emits public creation kits with exact definition pins
for native and SDK hosts. Transfer its independently obtained SHA-256 alongside
the catalog through a trusted installation; a self-declared checksum does not
authenticate a publisher. `prim-library check-pack <folder>` validates a local
record against its lock without printing its private values. Both commands are
local and execute no profile code. See
[the offline host contract](../../program/OFFLINE-HOST-CONTRACT.md).
