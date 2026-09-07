# Second CI failure and D007 — self-contained SDK fixtures

Observed run: https://github.com/primfoundation/prim/actions/runs/34057666087
Head: dae130d2dc5ddcfd33e2c02db81207153490cbff
Job: 101552409222; retained artifact: 9996461110.

All six bootstrap commands passed again. The SDK passed the corrected host
assertions and then failed because it tried to open a missing sibling
prim.obf/examples/metrics-gold-fairy-tale directory. The old test intended this
example to be optional, but caught only a no-index.md error; openPrim correctly
throws not-found when the entire directory is missing. registry.test.ts did
not run because the package script joins the two commands with &&.

## D007 — Eliminate environment-dependent coverage without weakening checks

Status: bounded test-only implementation decision; rerun and review required.

Always build a tiny synthetic local book pack and exercise every original book
assertion against it. Preserve the optional real sibling example, but test its
presence explicitly. When it exists all assertions still run and errors are
not swallowed. When it is absent the output explicitly identifies that skipped
integration example; it is not presented as tested. No runtime file or old
format changes. The synthetic fixture proves SDK contracts, not independent
OBF profile conformance or a real-world book implementation.

This remains within D006's single-existing-test-file scope exception. Keep both
CI failures, do not hide the SDK command, and require a fresh observed run.
Next worker: check the latest PR #5 verification run before claiming green;
then proceed to actual ORF fixtures and differential compatibility tests.
