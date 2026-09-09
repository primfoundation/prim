# Local artifact capture into Research — prototype 0.1

Requirements: ING-001, bounded portion of ING-002, RES-002 and RES-004.
Library 0.1.0a3 ships `capture-research` and `check-capture`. The native Research
0.3.0-dev.3 definition and all existing pins remain unchanged. This is an
experimental local connector, not automatic semantic extraction or a new
ratified universal artifact type.

## Run the local example

Copy `services/library/examples/research-capture` into a working directory.
Its source text and recorded storage permission are synthetic tutorial data.
After installing the reviewed Library wheel or an immutable Git-source version:

```bash
prim-library capture-research ./research-capture/capture.json --version 0.3.0-dev.3 --output ./research-draft
```

The command prints counts, the operation digest and a `receipt_sha256`. It does
not print original source contents, source URLs, permissions or private record
values. Preserve that receipt digest through a trusted channel when transferring
or checking the folder:

```bash
prim-library check-capture ./research-draft --expected-sha256 RECEIPT_SHA256
prim-library check-pack ./research-draft
```

`check-capture` verifies the original bytes and the initial record, lock, face
and log. `check-pack` only validates the current Research record and definition
pin. They answer different questions. Later legitimate record edits make the
initial capture integrity check fail; retries never overwrite those edits.
The original capture should be retained separately when beginning revisions.

## Explicit source selection and provenance

A manifest has format `prim-artifact-capture`, version 1, an `operation_id`,
a title, a question (or null), and 1–128 source records. Each source requires:

| Field | Meaning |
| --- | --- |
| `id` | Caller-selected stable source identity; duplicate identities fail. |
| `path` | Explicit local file, relative to the manifest unless absolute. URLs and directories are not read. |
| `locator` | Source identity/location as recorded; never fetched. |
| `sha256` | Expected original file bytes, obtained during the caller's prior inspection. A checksum is not source authentication. |
| `media_type` | Type/subtype as recorded; no content sniffing or parser is run. |
| `observed_at` | Timezone-aware ISO timestamp as recorded, or null when unknown. |
| `permissions` | Boolean `may_store` and `may_share`, plus `basis_as_recorded`. Storage must be explicitly true. This is not authenticated authorization. |
| `extensions` | Optional bounded metadata object, retained without interpreting it as instructions. |

The top-level optional `extensions` is also retained. The resolver's namespace
policy is not reused as a grant to read private sources. Ordinary filesystem
access still applies, and the caller must select appropriate files and supply
the recorded storage basis. No account, browser, credential store or source URL
is accessed. This command never adds permissions or uploads anything.

## Result and identity

The new private folder contains the ordinary `research.json`, definition lock,
`index.md` and `log.md`, plus `ingestion-receipt.json` and
`artifacts/<original-sha256>.bin`. Binary contents survive byte-for-byte, including
line endings and invalid UTF-8. Identical bytes use one blob but retain separate
source records, locators, permissions and IDs. Byte deduplication is not entity
resolution or a finding of independent corroboration.

The Research record stays a draft with an unresolved outcome. Its sources carry
artifact digests, lengths, relative blob paths, recorded metadata and capture
time. Claims, evidence links and reviews remain empty. Source capture never
changes a citation into support or certifies factual accuracy. The receipt
records captured bytes and structural checks separately from unverified
permission, authorship, event time and truth.

Observed filesystem modification time is an exact **decimal string of
nanoseconds**, preserving precision across Python/JavaScript/native numeric
limits. The observed POSIX mode is metadata, not a reproduced access grant.
Output directories/files use 0700/0600 on POSIX even when recorded sharing is
allowed. Owners, ACLs, extended attributes, executable bits, signatures and
source filesystem timestamps are not restored onto the copied blob.

## Safe retries, updates and transfers

Operation identity hashes the manifest without original paths plus the exact
Research definition pin. Source ordering is normalized by ID. Retrying the same
operation into the same destination verifies the existing receipt, all captured
bytes and initial Prim files, then returns `replayed` without changing them.
Original files can have moved or disappeared. Retry means verify the prior
capture; it does not promise that the external source is still current.

A changed request, digest, permission or definition pin conflicts with an
existing destination. Capture a new revision into a new folder with a new
operation ID. Optional extensions can record a prior receipt digest as lineage;
that link is caller-recorded, not authenticated supersession or an automatic
change to earlier evidence. Idempotency is scoped to the selected destination,
not a global operation-ID registry.

Transfer the **complete folder** and check it with the retained receipt digest.
The installed smoke removes both original source and manifest, copies the whole
folder and verifies it. The current TypeScript reader independently validates
the captured record and preserves its metadata. Its ordinary record exporter,
the Hub ZIP workbench and Primboard's record export are not full attachment
transports: do not use a record-only export as a backup of captured evidence.
No attachment migration across those exporters is claimed by this increment.

## Bounds and failure behavior

Sources: regular files only, up to 4 MiB each and 16 MiB total input work,
including duplicates. Archives, nested archives and scripts can be retained as
opaque bytes within those bounds; they are never expanded or executed. Symlinks
and special files are rejected. Changes to size/modification/change timestamps
while a file is read fail the capture. This assumes a trusted local tree, not a
sandbox against a hostile process racing ancestor directories.

Manifest, receipt and Research authority JSON each stay within 512 KiB. Existing
JSON depth/container and schema limits apply. Metadata numbers must fit the
portable host magnitude of 2^53−1; use explicit strings for larger exact values.
Object keys must already be NFC; no lossy normalization is performed. Unknown
metadata within these limits is retained rather than silently discarded.

All source reads and checks complete before a destination is published. Staging
failures clean up the staging directory and leave originals alone. An unrelated
existing destination, missing or changed attachment, corrupted receipt or later
record edit fails without replacement. This is not physical power-loss durability,
a resumable streaming transfer or a concurrent cross-device transaction service.

Remaining ING acceptance includes authenticated remote connectors, real source
ACL enforcement and revocation/deletion propagation, controlled extraction and
inference policies, recursive encrypted/media parsing, cancellation/backpressure,
remote retries/costs, independent review and representative real-use exercises.
