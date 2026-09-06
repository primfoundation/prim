# Bootstrap evidence — September 6, 2026

> Historical pre-publication record. The 403 was subsequently resolved. Current
> publication and verification evidence is recorded in HANDOFF.md; new verification
> runs do not overwrite local-tests.json. The observations below describe the
> original standalone bootstrap run, not the current branch state.

## Implemented locally

A portable PROFILE.md package inspector/discovery compiler; deterministic local
catalog generation and drift checking; Research as the first publication
example; and a structured Foundation-wide delivery plan with dependency,
coverage, evidence-stage and generated-roadmap checks.

The implementation has negative cases for malformed/unsafe YAML, duplicate
keys and IDs, invalid versions, missing/traversing/symlinked resources, size and
nesting limits, bounded discovery, and a declared validator that must not run.
Program tests reject fake completed states, missing evidence stages, unknown
references, cycles, orphaned coverage, and roadmap drift. They do not prove
security against every attack or factual correctness of research contents.

## Actual verification

`local-tests.json` is the authoritative machine-readable record for the latest
local run. It retains each command, exit code, stdout/stderr, test count,
environment, and SHA-256 digests of the tested new code/data. Regenerate it with:

```bash
python tools/verify.py
```

Before that run, regenerate intentional source changes with the commands in
program/README.md. The verification command checks generated output, rather
than silently fixing drift.

## Not established

No full repository checkout or existing TypeScript/ORF/UI regression run;
no remote commit, PR, CI result, published package, deployment, activated system,
independent security review, or real-user/account acceptance.

GitHub rejected both attempted tree creation and branch creation with HTTP 403
`Resource not accessible by integration`. Source files and the intended branch
were not written remotely. All new files are preserved in a reviewable change
set. Existing formats and production behavior are unchanged.

Only manifest structure and declared local resource paths are currently checked
for Research. Profile-instance validation, namespace verification, full-package
integrity, remote installation and legacy migration remain explicitly open.
