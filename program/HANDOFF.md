# Publication handoff — September 6, 2026

## Published and tested checkpoint

GitHub authorization is restored. PR #5 is open, not merged:
https://github.com/primfoundation/prim/pull/5

Branch: `codex/foundation-program-bootstrap`.
Base main: `08760405325ca3f9c9b63648c7398ffc4c96e831`.
Tested code head: `4eb5b456d0c2591a754f1e5c03d97680072e17a2`.
Tested code tree: `1f362cf16626ff112e545ca11dff8f0ebff22484`.

Commits preserve the bounded steps:
- `844285cd9e8c13e5038378f9602f77abb1b6d19d`: bootstrap publication.
- `d546b8408f671c557eef976c64e87f0b6fbd128a`: full-checkout CI configuration.
- `dae130d2dc5ddcfd33e2c02db81207153490cbff`: stale host expectations corrected.
- `4eb5b456d0c2591a754f1e5c03d97680072e17a2`: self-contained book fixture.

This evidence checkpoint changes documentation only. The latest PR checks
identify the documentation commit's own verification status; do not confuse a
record of an earlier passing code head with a claim about an unobserved run.

## Verification actually established

Full-checkout CI run 34057807656 completed successfully at 2026-09-06T20:23:12Z:
https://github.com/primfoundation/prim/actions/runs/34057807656

All seven verification commands passed: 44 bootstrap unit tests, ledger check,
roadmap drift, catalog drift, Research manifest inspection, Python compilation,
and the SDK command running pack.test.ts followed by registry.test.ts.
The full report was downloaded and its ZIP digest matched the artifact service.
See evidence/ci-34057807656.json for identifiers, digests, outcomes and limits.

The SDK always exercises local book-contract assertions. The optional external
prim.obf example was absent and explicitly reported as skipped. No real OBF
profile interoperability, ORF legacy validation, UI, package installation,
independent security review, deployment or real-account acceptance is claimed.

The original standalone ZIP checksum manifest and 44 tests were also verified.
The initial 26-file publication tree dd37619ac533cede3e10ce4290d1945e95557367
matched independent hashing of local bytes and preserved baseline subtrees.
Subsequent diffs were checked to contain only documented test/evidence changes.
Local direct checkout still failed DNS; CI provided the complete checkout.

## Failures retained and scope boundary

Run 34057476987 passed the bootstrap but found two stale SDK tool lists that
omitted already-registered prim-mac and prim-web hosts. Run 34057666087 passed
the corrected lists but exposed a test's implicit sibling-repository dependency.
D006 and D007 record the test-only fixes and their evidence. No check was
silently bypassed: strict lists remain, host filters gain assertions, and all
book assertions now run on an always-present synthetic fixture. Available but
malformed sibling fixtures still fail; absent optional integration is explicit.

One existing test file changes. Existing production runtime, legacy registry,
formats, person/ORF code, unrelated branches, main and production are untouched.
No package is published and no unattended agent or paid worker is launched.
The PR workflow is bounded verification, not autonomous implementation.

## Next concrete step and acceptance

Review PR #5 and preserve every open gate. Then begin RES-001: retrieve a pinned
ORF source snapshot and its real positive/negative fixtures; run the original
validator and retain outcomes; add differential tests before any Research vNext
adapter. Completion requires preserved originals and explicit interpretation/
loss handling, not an alias or rename. Research instance validation is not yet
implemented. Reconcile docs/opf and independent branch work before cutover.

The 17-workstream, 70-requirement ledger remains canonical. Publication and
passing CI do not imply independent review or a complete Foundation milestone.
No auto-merge or production deployment is enabled by this checkpoint.
