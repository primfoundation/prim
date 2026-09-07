# Publication and first CI evidence — September 6, 2026

PR: https://github.com/primfoundation/prim/pull/5
Base: 08760405325ca3f9c9b63648c7398ffc4c96e831
Initial published head: d546b8408f671c557eef976c64e87f0b6fbd128a
Initial published tree: dd37619ac533cede3e10ce4290d1945e95557367

The branch was created, both commits written and the ref advanced without
force. The PR initially contains 26 added files and zero deletions. Its full
tree matched independent local Git object hashing, including unchanged original
subtrees. Archive-only application instructions remain in the original ZIP.

## Actual test outcomes

The local standalone rerun at 2026-09-06T20:17:06.259200+00:00 passed 44 unit
tests and all six bootstrap verification commands. Runtime: Linux, Python
3.13.5 and PyYAML 6.0.3. This was not a local full checkout.

GitHub Actions run 34057476987 checked out the complete repository at PR merge
ref 9fce2941244bc5de945b1e4c4dc9e7f28ac4e146 (the branch was NOT merged into
main). Job 101551894348 used Ubuntu 24.04, Python 3.13.15, PyYAML 6.0.3 and
Node 22.16.0. Bootstrap unit tests, ledger validation, roadmap drift, catalog
drift, Research manifest inspection and compileall all returned success.
The seventh command, npm --prefix sdk/typescript test, returned failure.

Retained report artifact: 9996410003, prim-foundation-verification.
ZIP SHA-256 reported by the artifact service:
04ffe074633f764cc8778ab6120dd7e90e9fa83ea38b335f59bca11f4a13790a

## D006 — Reconcile stale host expectations, not runtime behavior

Status: bounded implementation decision, with rerun and review still required.

Failure at sdk/typescript/tests/pack.test.ts:194: expected
opff-editor, prim-viewer, prim-viewer-webmcp; actual additionally includes
prim-mac and prim-web. Another OCSF expectation has the same omission.
Inspection of the unchanged Pack.tools() confirms it includes every wildcard
citing tool, and the unchanged registry.test.ts explicitly expects four
wildcard tools. The production registry already lists both hosts.

Correct those two exact expectations to include the existing hosts, retaining
profile-editor precedence. Add an explicit surface/host filter check for the
two hosts and a connector/host check that must be empty. Do not change the
runtime, remove a test, loosen strict equality, or drop the SDK CI command.

This narrowly supersedes the additive-only safeguard in D004 for one existing
test file only. All production source, old formats, registry data, and
unrelated work remain untouched. Later CI evidence must identify its own
commit/run and actual outcome. Neither a fixed expectation nor an artifact
hash is proof of broad interoperability, security, release or deployment.
