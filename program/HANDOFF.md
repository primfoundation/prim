# Publication handoff — September 6, 2026

## Current checkpoint

GitHub write access was restored after the founder added the organization. The
connector created `codex/foundation-program-bootstrap` from main
`08760405325ca3f9c9b63648c7398ffc4c96e831`. Main was unchanged on re-read and the
open-PR collection was empty before publication. The earlier 403 remains
historical evidence, not a current blocker.

This is the preserved bootstrap plus a verification-runner correction: new runs
no longer assert the old access failure or overwrite the historical local test
report. `python tools/verify.py --with-sdk` also requests the existing SDK tests
and records failure rather than implying a pass when unavailable.

The original ZIP checksum manifest was verified and its 44 tests rerun locally.
This local workspace still contains only the additive change set: direct Git
checkout failed because github.com could not be resolved. Full-checkout CI must
be observed independently. Review the pull request's checks and changed files;
this handoff is not evidence that CI, review, release or deployment passed.

## Preserved scope

The charter, decisions, baseline, 17-workstream/70-requirement ledger, generated
roadmap, profile package contract, Research prototype, local discovery compiler,
generated catalog, ledger checker, tests and original evidence are preserved.
No requirement becomes complete merely from publication. Archive-only APPLY.md,
START-HERE.md and SHA256SUMS are kept in the downloadable original bundle rather
than installed as permanent repository instructions. No existing source file
or legacy registry entry is overwritten.

## Next gate

Finish the atomic branch commit, verify its remote blob hashes against the
reviewed local files, open a pull request, and observe the bootstrap and legacy
SDK test results in a full checkout. Preserve failures as failures. Update the
ledger after those events actually occur; never infer release or deployment.

Then pin actual ORF source and fixtures, run the original validator, and add
differential compatibility coverage before implementing a Research vNext
adapter. Reconcile the existing category, docs/opf plan, semantic-substrate draft,
and independent branch work. Namespace and Research semantics remain development
choices; the orf metadata alias is not a migration.

Existing sdk-python and prims/zeroshot-connector branches remain untouched.
No production service, package release, paid worker or unattended continuation
has been started. A bounded pull-request test job is validation, not a research
agent or permission to change production. Consult the next checkpoint for exact
commit/PR/CI identifiers once those are available.
