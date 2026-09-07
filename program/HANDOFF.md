# Foundation execution handoff — September 7, 2026

## Current state

The Foundation bootstrap (#5), ORF compatibility (#6), Library/MCP alpha (#7) and sanitized Workbook import (#10) are merged into `primfoundation/prim`. The reorganization branch (#8) is reconciled with their shared main baseline; its current PR metadata is the authority for its submitted head and final integration state.

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

## Next actionable gates

1. **Cloudflare:** the [isolated Hub preview](https://prims-hub-preview.eidos-agi.workers.dev/) is deployed with the exact tested module and all five Static Assets. Version `03266017-e4df-42f4-beda-fe656a095767` receives 100% in deployment `fabf4b0e-a170-41d8-9014-652869273d5c`. The upload blocker was traced to Cloudflare MCP adding account authorization alongside the special upload JWT; a separate HTTPS uploader using only that temporary token succeeded. No reconnection or broader credentials were needed. The homepage was observed live and the external MCP SDK completed initialize/list_tools. Hosted CI `34146877288` passed all four canonical kits and public HTTP/assets/security boundaries through the external SDK in auto and legacy modes at test commit `2e7d3d8e…` (`prim-web` PR #7). [Deployment evidence](evidence/2026-09-07-cloudflare-deployed.json) preserves the initial client failures and the verified scope. Establish operator/cost ownership, edge limits, monitoring and recovery; prove real Apple/session/container flows before any browser-service cutover. Separate workers.dev hosts cannot share host-only login cookies.
2. **Desktop:** recover the authoritative `../prim-sim` checkout and its remote/revision/license. Both candidate GitHub lookups returned 404 through the current account, which does not prove deletion. Do not replace `PrimSimCore` with a guessed URL or stub. Preserve existing PRs #2/#3/#4/#6 and their FDA/XPC/signing gates until reproducible source and Mac proof exist.
3. **Primboard:** implement encrypted index migration and tested recovery/backup, then generic Library conversion and signed existing-store acceptance. The merged file replacement is atomic per file, not a multi-file journal. Locking requires updated binaries; mixed old/new writers remain unsupported.
4. **Governance/migrations:** obtain actual admin/reporting controls and ownership evidence; complete remaining source/consumer/privacy audits. No archive, rename or visibility change follows automatically from consolidation docs. Independent review and real-use evidence remain separate from our automated checks.

## Stable boundaries

Private Prim instances stay local/user-owned. The public Hub distributes definitions and public metadata. Popularity has no fabricated launch signals and does not mean truth, safety or official status. Primboard and Desktop bundle/CLI/Keychain/store/signing identities remain fixed. Valid legacy browser session cookies remain compatible; restart old in-flight Apple logins when a future nonce-enforcing cutover occurs.

No production DNS or route change, repository archive/rename, history rewrite, signed release, private data upload or paid unattended worker was performed. No background agent is running. `plan.json` remains the canonical ledger; regenerate `ROADMAP.md` with `python tools/program.py render` after edits.
