# Major-goal execution status — September 7, 2026

`MAJOR-GOALS.md` defines completion. The 79 requirements in `plan.json` and its generated `../ROADMAP.md` retain the wider obligations. Exact commits and CI live in `evidence/2026-09-07-execution.json`.

| Goal | State | Current proof | Next gate |
| --- | --- | --- | --- |
| G1 Canonical standards | in progress | Bootstrap, ORF compatibility, Library/MCP and Workbook merged; 53 Library tests, 96 Foundation Python tests, both TS suites and clean installed wheel pass | stable identity/distribution and broader incubator migrations; independent implementation/review |
| G2 Public Hub | in progress | Hub PR #5 merged; four canonical profiles generate human pages/API/MCP; real local Worker and external MCP client parity pass in CI `34086822519` | Foundation Cloudflare installation/connection and approved account/domain; public preview acceptance; old website/route migration, accessibility, monitoring and recovery drill |
| G3 Primboard | in progress | PR #1 merged; normal startup seeds disabled while old cards survive; serialized storage, stale-write rejection and atomic replacement; 121 Mac tests, release build and isolated selftest pass in CI `34086141864` | encrypted index, multi-file transaction recovery, backup/restore, generic conversion, signed-Mac/TCC and real existing-store acceptance |
| G4 Browsers | in progress | Both Worker apps imported with provenance and shared session/assets; signed Apple identity verification and fail-closed authentication; 13 tests and both dry builds pass in CI `34086860578` | shared preview cookie domain and real Apple/session/container acceptance; production routes and rollback drill before archive |
| G5 Desktop | blocked on source | PR #7 merged: source proof fails honestly when required dependency is absent; open integration PRs #2/#3/#4/#6 preserved | recover authoritative `prim-sim` / `PrimSimCore` source, revision and license; reproducible clean Mac build; then generic Library host and signed device acceptance |
| G6 Incubator migration | in progress | Sanitized Workbook profile imported from exact `8e997f0e…` source with preserved legacy blobs; ORF baseline retained | remaining per-repository privacy/semantics/consumer audits; separate hybrid viewers/runtimes; real consumer acceptance |
| G7 Institutional durability | in progress | `.github` defaults merged; canonical program reconciled; Hub/browser deployment and rollback procedures committed | administration, private reporting, ownership/cost records, independent review and actual restore/rollback exercises |

No goal is complete solely because an implementation is merged or CI passes. No repository rename/archive, production DNS/route cutover, signed release or private-record upload is claimed.
