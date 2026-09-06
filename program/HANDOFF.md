# Publication handoff — September 6, 2026

## Published checkpoint

GitHub authorization is restored. PR #5 is open, not merged:
https://github.com/primfoundation/prim/pull/5

Branch: `codex/foundation-program-bootstrap`. Base main:
`08760405325ca3f9c9b63648c7398ffc4c96e831`.

Bootstrap commit: `844285cd9e8c13e5038378f9602f77abb1b6d19d`.
Full-checkout CI configuration commit: `d546b8408f671c557eef976c64e87f0b6fbd128a`.
The 26-file publication tree `dd37619ac533cede3e10ce4290d1945e95557367`
was independently reconstructed from local bytes and preserved baseline
subtrees and matched the remote tree exactly. This is transfer integrity,
not semantic correctness or a security certification.

The original standalone archive checksums and all 44 tests were verified again.
A fresh local run at 2026-09-06T20:17:06.259200+00:00 passed all six bootstrap
commands. Direct local Git checkout still fails DNS; repository-wide execution
is now performed by the explicitly configured GitHub PR workflow instead.

## Full-checkout evidence and bounded test correction

First CI run: https://github.com/primfoundation/prim/actions/runs/34057476987
Job: 101551894348. Completed with failure at 2026-09-06T20:17:23Z.
All six bootstrap commands passed, but the existing TypeScript SDK test failed
at pack.test.ts:194. It expected three tools where the existing registry and
Pack.tools() return five: the profile editor, viewer, viewer connector, Mac
host and web host. The untouched registry test independently expects four
category-wide tools. No bootstrap runtime file caused the extra hosts.

Decision D006 is recorded in program/evidence/2026-09-06-publication.md:
correct the two stale exact tool-list expectations and add positive/negative
host-filter assertions. Keep every earlier check; change no SDK runtime or
registry data. This is the sole exception to the bootstrap's additive-only
scope. The first failure remains retained, not relabeled as a pass.

Observe CI on the test-correction commit before claiming the SDK is green.
New verification reports are retained as workflow artifacts; the original
local-tests.json and access-blocker.json remain historical evidence.
Independent review, package installation, ORF validation, desktop/UI checks,
release, deployment and real-user acceptance are not established here.

## Next implementation gate

After CI is observed and any actual failure resolved, pin the ORF source and
fixtures, run its original validator, and establish differential compatibility
coverage before a Research vNext adapter. An informational orf alias is not a
migration. Reconcile the category, docs/opf plan, semantic-substrate draft and
independent branches before any broader cutover.

The 17-workstream, 70-requirement plan remains canonical; no requirement is
complete merely because this PR is published. Existing sdk-python and
prims/zeroshot-connector branches, main and production remain untouched.
No package release, paid agent worker, or unattended continuation is started.
PR CI is a bounded test job with read-only repository access and no deploy step.
