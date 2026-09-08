# Foundation execution handoff — September 8, 2026

## Current state

The Foundation bootstrap (#5), ORF compatibility (#6), Library/MCP alpha (#7) and sanitized Workbook import (#10) are merged into `primfoundation/prim`. The reorganization work (#8) is merged at `cc640009089cd8663021fbd6a8211c7a605c68ea`. September 8 Hub and Primboard release work is recorded in `evidence/2026-09-08-release.json`.

Four development profiles are available through generic local creation tooling: Research, Person, Decision and Workbook. Source/workbook provenance is preserved; no customer-history import or stable-standard release is implied. All 17 workstreams, seven milestones and 79 requirement IDs remain. Whole-life contexts, diagnostics, ingestion, authority/privacy, governance, community, sustainability and the remaining diverse reference cases are still obligations.

## Integrated product increments

| Repository / PR | Result | Evidence |
| --- | --- | --- |
| `prim` #10 | Workbook provenance fix, immutable source regression, rebuilt four-profile Library | tested `86e8a58c…`; CI `34085213081` / `34085213070`; 53 Library + 96 Foundation Python tests, both TS suites, clean wheel and installed MCP smoke |
| `prim-web` #5 | canonical bundled Hub catalog, human pages, JSON/MCP and local-authoring kits | tested `dfe683cc…`; CI `34086822519`; six tests, dry build, real local Worker HTTP + external auto/legacy MCP parity for all four kits |
| `prims-paste-desktop` #1 | safe startup, current-version store locking, revision conflict rejection and atomic replacement | tested `d0fae3b9…`; macOS CI `34086141864`; 121 XCTest cases, release build, isolated selftest and compatibility guards |
| `prims-browsers` #1 | imported login/gateway Workers; shared session/assets; verified Apple identity and fail-closed configuration | tested `e542cd69…`; CI `34086860578`; 13 tests and two dry builds; complete synthetic Apple-to-gateway round trip |
| `prims-desktop` #7 | required-source/toolchain preflight prevents false successful proof | tested `075128f3…`; Bash syntax + real missing-dependency failure; no native pass |
| `.github` #1 | contribution, security, repository lifecycle and evidence defaults | document contents inspected; merged `350af7fe…`; no admin enforcement or independent review claimed |

All rows above are merged. Full tested and merge SHAs, scope and limitations are in [execution evidence](evidence/2026-09-07-execution.json). A CI result belongs to its exact tested commit, not arbitrary later work.

## September 8 shipped increment

- **Hub:** searchable discovery, readable specifications, connection onboarding, generic local creation/edit/validate/read/save/open for four pinned profiles and a downloadable offline workbench. Tests preserve unknown fields and declared Research relationships. Focused-field and stale-download-link regressions were found during hosted acceptance and fixed. The release evidence records exact artifacts, module/assets hashes, source commits, deployments and public HTTP/MCP checks.
- **Primboard:** PR #2 merged at `26fa1162c4569f2e2f87c4c4ffabc792f9aa4231`. The `PPI3` encrypted index envelope preserves an encrypted exact-byte legacy backup before migration; referenced legacy payloads authenticate with the existing key first. `prims-paste backup` and `restore … --to …` authenticate all referenced data, refuse replacement and restore to a new directory. CI `34175616470` and merged-main CI `34175780056` pass the 131-case suite, release build, isolated selftest and compatibility guards. No signed binary or private-store migration was performed here.
- **Operations:** the previous Cloudflare catalog was restored at 100%, observed live, then the current workbench version was restored and observed. A six-hour public health workflow is configured. Exact drill versions and deployments are retained; it was limited to the isolated preview.

## Next actionable gates

1. **Hub acceptance:** automated compiled-UI saves and round trips pass. Hosted browser creation, focused edits and synthetic file reopen were observed, but download events timed out; do not claim confirmed browser-to-disk completion. Phone/screen-reader/accessibility and independent user acceptance remain open. Record fields stay local; the public service distributes only definitions.
2. **Public operations:** establish named operator/cost ownership, escalation destination, SLOs and edge quotas. Reconcile the legacy Railway `Service not found` failure and old website/route ownership before production cutover. The new Cloudflare endpoint's HTTP/MCP checks pass separately. A working MCP protocol is not proof of installation in a particular ChatGPT/Claude host.
3. **Primboard:** ship the signed real-Mac acceptance gate for existing-store reopen, Keychain reuse and TCC. Use the updated app and CLI together: old JSON-only readers fail on the encrypted index. Same-key backups cannot recover a lost key. A multi-file crash journal, guided GUI recovery and generic Library conversion remain open.
4. **Desktop:** recover the authoritative `../prim-sim` checkout and its remote/revision/license. Prior candidate lookups returned 404, which does not prove deletion. Do not stub `PrimSimCore` or guess its source. Preserve existing PRs #2/#3/#4/#6 and their FDA/XPC/signing gates.
5. **Browsers/governance/migrations:** prove real Apple/session/container behavior and shared cookie-domain routing before cutover. Complete remaining source/consumer/privacy audits, actual administration/reporting controls and independent review. No rename/archive follows automatically from consolidation documents.

## Stable boundaries

Private Prim instances stay local/user-owned. The public Hub distributes definitions and public metadata. Popularity has no fabricated launch signals and does not mean truth, safety or official status. Primboard and Desktop bundle/CLI/Keychain/store/signing identities remain fixed. Valid legacy browser session cookies remain compatible; restart old in-flight Apple logins when a future nonce-enforcing cutover occurs.

No production DNS or route change, repository archive/rename, history rewrite, signed release, private data upload or paid unattended worker was performed. No background agent is running. Bounded repository CI and the configured public health workflow are the only unattended checks added. `plan.json` remains the canonical ledger; regenerate `ROADMAP.md` with `python tools/program.py render` after edits.
