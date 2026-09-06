# Research compatibility: preserve first, interpret explicitly

Status: reference implementation, under review. This is not Research vNext 1.0,
a published SDK, a registry cutover, or permission to reinterpret historical ORF.

## Immutable legacy baseline

`orf-0.2.0/upstream/` contains all 15 tracked files from
`eidos-agi/prim.orf` commit `4ae78ddaec19ebbc2c1e93f8289e9c6993af057d`,
tree `bcaa23d1bd32bce7e627538abb107d98799cebaa`. No upstream byte was edited.
The original MIT license, specification, agent guidance, package metadata,
validator and positive/negative examples remain alongside one another.
`orf-0.2.0/baseline.json` records file sizes, SHA-256 and Git blob identities.
The root baseline tree was obtained through read-only CI run 34059269453;
source archives excluded Git credentials and were not executed during acquisition.

`python tools/research.py verify-baseline` checks the retained inventory before
the compatibility reader loads the reviewed legacy validator. This is a local
integrity check, not independent authentication of the publisher or research.
`python tools/orf_conformance.py` executes the unchanged legacy CLI, including
its self-test and both example packs in default and strict mode. It also compares
inspections before/after byte-preserving transport for both packs and both modes.

## Working local tools

From the repository root:

```bash
python tools/research.py inspect path/to/orf-pack --strict
python tools/research.py preserve path/to/orf-pack --output /tmp/research.orf-preserved.json
python tools/research.py restore /tmp/research.orf-preserved.json --output /tmp/restored-research
python tools/research.py render /tmp/research.orf-preserved.json --output /tmp/research-review.html
```

Outputs must be new paths. Source packs are never overwritten, and outputs inside
a source pack are refused. A directory or this tool's explicitly identified JSON
preservation transport is accepted; `.prim`/ZIP/TAR import is not implemented in
this reader. The legacy SDK's existing archive support is not a safety claim for
this implementation. No network access, source URL retrieval, telemetry, profile
installation, arbitrary validator imports, or scripts embedded in records run.

The browser view is offline, script-free, and escapes document content instead of
interpreting supplied Markdown/HTML as executable markup. It is a derived review
view, not a new canonical editor. Browser accessibility/visual acceptance and a
real cross-application workflow remain open.

## What is preserved; what is not

The preservation transport is `prim-orf-preservation`, version 1. It records a
bounded ordered inventory, Base64 file bytes, SHA-256 content digests, and empty
directories. Identity is a digest of canonical relative paths, byte lengths,
content digests and directory layout. It is a change detector, not an object
identity standard or a signed attestation.

Original file bytes (including binary attachments, CRLF, malformed UTF-8 and
unknown fields), names and empty directories round-trip exactly. OS owners,
permissions/executable bits, timestamps, extended attributes, original archive
bytes and external resources do not. The transport says so. It is not an install
package: restored files deliberately do not recover executable permissions.
The original pack remains the semantic authority. Transporting bytes is not
migration to a Research schema; no fresh approval or factual support is invented.

The inspector exposes both historical-subset and safe YAML interpretations when
they differ. It retains complete original documents and hashes. Its research
preview groups the question, recorded brief/status/approval and finding citations
for a human/agent. It is explicitly `authoritative: false`; `cites` does not imply
`supports`, a retrieved source, independent evidence or a verified conclusion.

## Validation dimensions

`legacy_validation` reports `passed`, `failed`, `engine_error`, or `not_checked`.
It selects only the observed ORF 0.2.0 / OKF 0.2 declarations. A newer version,
conflicting profile, missing declaration or excessive Markdown size is not
silently accepted. CLI inspect exits 0 for legacy pass, 1 for legacy rejection,
2 for unavailable/errored checks or unsafe inputs. Review warnings remain visible
even when the legacy oracle returns success; they are not silently redefined as
new legacy failures.

Separately, Research vNext conformance, factual accuracy, source independence,
reviewer identity, authority and source retrieval are explicitly unverified.
Every file not covered by the legacy validator is listed. `log.md` and opaque
evidence being preserved does not mean their contents were validated.

## Characterized historical gaps (do not repair the frozen baseline)

| Counterexample | Historical behavior | Compatibility-reader treatment |
| --- | --- | --- |
| Finding without frontmatter | Can pass, including strict pack validation | Report missing/unparsed metadata and completeness warnings. |
| Face without `status` | Can pass | Retain it, warn; do not invent workflow completion. |
| Scalar `verified` instead of mapping | Can raise `AttributeError` | Report `engine_error`, never success. |
| Duplicate YAML key | Subset parser keeps the later value | Preserve bytes and historical result; comparison reader rejects ambiguity. |
| Inline comment or block scalar | Subset parser can disagree with YAML | Show both interpretations; block automatic semantic migration. |
| Two subdomains of one site | Counted as two hosts | Never claim independent sources were established. |
| `--strict` for a single finding file | Some warnings are not promoted | Preserve the baseline; characterize this separately from strict pack behavior. |
| Missing/unrecognized declaration | May be treated as generic Markdown by historical paths | This reader reports the profile check as not performed. |

These are testable implementation observations, not a criticism based on new
standard rules. Do not rename labels or fix these inside the pinned source.
Research vNext should address them through an explicit versioned model and
migration decisions with fixtures.

## Remaining migration gate

RES-001 is still in progress: source preservation, historical characterization,
transport round trips and a loss report exist. A semantic Research vNext migration
and independent review do not. RES-002 must define the target contract first.
Unknown fields, ambiguous parsing, citations, evidence grades, identity, review,
revision history, and authorization need explicit interpretation/loss decisions.
