# Research compatibility handoff — September 6, 2026

## Scope and branches

The full Foundation program remains authoritative: 17 workstreams, 70 requirements,
seven milestone gates. Research is the first path, not the mission boundary.
Whole-life Worlds, Coverage/Fidelity/Operability diagnostics, six reference cases,
security, human products, governance, ecosystem and sustainability remain open.

Bootstrap: PR #5, `codex/foundation-program-bootstrap`, observed head
`633ae194ff96de6d1e9bf43dad91aa7f066a474f`; its CI passed. It is not merged.
Continuation: PR #6, `codex/research-compatibility`, stacked on the bootstrap.
https://github.com/primfoundation/prim/pull/6

The initial continuation commit b8c3e9f579486934a20169cda2ef2c9ec3af323f created
only a bounded read-only baseline-source acquisition workflow. Run 34059269453
passed and its public tracked-source artifact was verified. The temporary
acquisition workflow is removed from the final code slice; its commit and run
remain evidence. Ordinary Foundation CI now covers stacked pull requests too.

## Implemented here

All 15 original ORF source files plus license/spec/examples are frozen at commit
4ae78ddaec19ebbc2c1e93f8289e9c6993af057d. The reference tools provide baseline
integrity verification, historical CLI conformance, bounded inspection, exact
byte/layout transport and restoration, interpretation-difference warnings,
a derived research preview and script-free offline review HTML.

See profiles/research/compatibility/README.md, program/THREAT-MODEL.md and D008–D011.
`legacy_aliases: [orf]` still does not trigger automatic resolution or migration.
The preservation envelope is explicitly NOT a native Research instance encoding.
Nothing in the input package can supply executable validation code or authority.

## Evidence and honesty

The complete public source export hashes to the observed bootstrap tree, so local
verification now includes the actual existing SDK. Retained reports:
- evidence/research-local-tests.json: exact current local checks/input digests.
- evidence/orf-conformance.json: original CLI and strict/default round trips.
- evidence/2026-09-06-research-compatibility.md: source and implementation scope.
- PR #6 checks/comments: observed CI for each submitted head; do not infer success
  for a later commit from an earlier passing run.

Historical validator gaps are preserved and exposed, not silently repaired.
A legacy pass is not factual correctness, independent evidence, authenticated
review, authorization, security certification or Research vNext conformance.
No independent review, native vNext migration, UI acceptance, published package,
production deployment, real-account trial or unattended agent is claimed.

## Next concrete bounded step

CORE-001/RES-002: propose and implement the smallest native Research record model
covering questions, assertions, source/evidence relationships, contradiction,
uncertainty, provenance and separate review/authorization state. Exercise it
against the known legacy failures and the six non-research reference cases before
promoting any new universal envelope. Then add explicit semantic migration and
loss reports; byte-preserving transport alone does not finish RES-001.

Completion requires retaining unknown bytes/fields, never creating approval or
support that was not asserted, recording parser ambiguity, and demonstrating a
round trip across independently developed readers. Keep broader program and
all review/deployment/real-use gates visible; do not shrink scope to this tool.

## Safety and coordination

Main, original ORF repository, the old runtime/registry, person formats, production
services and unrelated branches are untouched. The inherited bootstrap test fixes
remain unchanged. No automatic merge, paid worker, schedule or background agent
is enabled. Verification workflows are bounded CI, not autonomous implementation.
Do not overwrite PR #5 or existing sdk-python / prims/zeroshot-connector work.
Cross-repository plan/owner and deployment reconciliation remain PRG-004 work.
