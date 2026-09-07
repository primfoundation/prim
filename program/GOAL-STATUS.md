# Major-goal execution status

This file is a concise execution view. `program/MAJOR-GOALS.md` defines completion; the wider program ledger remains authoritative for requirement/evidence stages.

| Goal | State | Current proof | Next non-negotiable gate |
| --- | --- | --- | --- |
| G1 Canonical standards | in progress | repository-independent profile discovery; Research/Person/Decision creation kits; frozen ORF compatibility; sanitized Workbook source identified at `prim.workbook@8e997f0e` | import first sanitized profile with provenance; permanent identity/distribution rules; more incubator migrations; independent implementation |
| G2 Public Hub | in progress | installable Library MCP; Cloudflare target architecture; `prim-web` PR #5 has Workers + Static Assets web/API/MCP preview build; CI run `34074018249` passed typecheck/tests + Wrangler dry build | actual non-production Cloudflare deployment; external MCP client; migrate existing website/routes; production cutover/monitoring/rollback/accessibility |
| G3 Primboard | in progress | user-facing Primboard rename on main; stabilization PR #1; Mac CI now green on `fc4ac8d` after finding/fixing Swift 6 calendar typing, developer-specific Docket paths, non-hermetic integration tests, and a false secret assertion | remove production backlog seeding without deleting existing cards; transactional/concurrent store; encrypted index migration; backup/recovery; generic Library conversion; signed-Mac/TCC existing-store acceptance |
| G4 Browsers | in progress | exact login/gateway source refs recorded; duplicated session blob consolidated into `prims-browsers` PR #1 with migration locks/tests | finish shared-contract CI; import both Worker apps/assets/config with provenance; non-production builds; real Apple/session/container acceptance before route cutover |
| G5 Desktop | in progress | generic-host charter plus open Mac integration PRs #2/#3/#4/#6 inventoried with their distinct acceptance gates | reconcile overlapping surfaces; generic pinned profile lookup/open path; Mac acceptance without weakening FDA/XPC/signing boundaries |
| G6 Incubator migration | in progress | Eidos `prim.*` inventory/classification candidates recorded; ORF baseline already preserved; sanitized Workbook head selected as first import candidate | first profile-only import; then per-repo source/privacy/consumer classification and split large hybrids |
| G7 Institutional durability | in progress | program/reorganization/reality ledgers; archive gates; `.github` PR #1 adds security/contribution/repository-lifecycle defaults and evidence-oriented PR template | admin rules/private-vulnerability/release controls; deploy/recovery manifests; security response; cost ownership; actual restore/rollback exercises |

Never convert `in progress` to complete from a single implementation or CI run. Completion requires the goal contract.
