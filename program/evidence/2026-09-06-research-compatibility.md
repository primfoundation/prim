# Research compatibility implementation evidence — September 6, 2026

Requirements advanced: RES-001, RES-002, SEC-001, INTEROP-001. PRG-003 records the
already-published bootstrap separately. All 17 workstreams, 70 requirement IDs,
seven milestone gates, coverage lenses and six reference cases remain in scope.
No requirement is marked complete by this change set. D008–D011 record decisions.

## Exact sources and acquisition

Read-only source acquisition run:
https://github.com/primfoundation/prim/actions/runs/34059269453

Artifact 9996944933 has SHA-256
`7ed4ce0c208deda3ad5493146e0bb1347867ae6766ccdf998d959d297dbdfcf5`.
The ZIP and both contained archive digests were verified before local use.
The Prim export is the full tracked source of commit
`633ae194ff96de6d1e9bf43dad91aa7f066a474f`; locally hashing the tree reproduced
`93d9db26f48ce461c6e74f3fb6c7499eb8e505ce` exactly. The locally initialized Git
commit is only an exported-source workspace marker, not the upstream commit.

All 15 files from ORF commit `4ae78ddaec19ebbc2c1e93f8289e9c6993af057d`
(tree `bcaa23d1bd32bce7e627538abb107d98799cebaa`) are preserved with their MIT
license and per-file SHA-256 and Git blob identifiers. No legacy byte changed.
The original CLI code was inspected before execution. It is run only from the
fixed reviewed baseline, never from input records or discovered profile code.

## Delivered behavior

- Verify the frozen source inventory and run the original CLI/self-test.
- Inspect bounded directory packs or an explicitly typed preservation envelope.
- Preserve and restore file bytes, canonical paths, unknown fields, binary
  attachments, CRLF and empty directories without overwriting originals.
- Compare historical and safe YAML interpretations; disclose ambiguity and
  legacy blind spots instead of silently rewriting meanings.
- Report legacy pass/failure/error/unavailable separately from unverified truth,
  source independence, authority, identities and Research vNext conformance.
- Produce a script-free offline browser review view and a non-authoritative
  research preview with question, recorded context/status and claim citations.
- Retain resource limits, threat boundaries and negative test cases.

These are reference tools, not a published production SDK or live website.
Semantic Research vNext migration, real evidence retrieval, native record editing,
independent implementations and authenticated review remain open.

## Verification

Run `python tools/verify.py --with-sdk` in the complete source checkout.
The suite includes the original bootstrap tests, new preservation/interpretation
and CLI tests, ledger validation, generated roadmap/catalog checks, inspection,
compilation, direct ORF conformance, and both TypeScript SDK test suites.
`research-local-tests.json` records actual commands, results and tested input
hashes. `orf-conformance.json` retains five original CLI executions (the two
negative exits are expected) and four exact before/after inspection comparisons.
CI on the submitted branch is a separate observation, not implied by local tests.

Known historical counterexamples are explicitly asserted, including empty finding
metadata passing strict mode, missing status, duplicate-key ambiguity, parser
disagreement, scalar verification errors, subdomain host counting and strict
single-file warning handling. The original behavior is characterized, not fixed.

## Limits and next gate

This proves byte/layout preservation and scoped interpretation, not a lossless
migration to a new research ontology. OS metadata and archive-container bytes
are not preserved. Filesystem safety assumes a trusted, non-mutating local root;
this is not a concurrent-adversary sandbox. Security and accessibility reviews,
actual-user acceptance, encrypted/remote distribution, release and deployment
are unperformed. Private records were not used or uploaded.

Next: CORE-001/RES-002 — define the smallest native Research record contract from
these counterexamples, then implement and differentially test semantic migration
with explicit ambiguity/loss handling. Preserve the original package even when
parts cannot be safely interpreted. Do not mark M2 complete from this slice.
