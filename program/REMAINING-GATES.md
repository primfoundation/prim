# Remaining delivery gates

The original Foundation scope remains intact. The 75% target does not remove unfinished requirements or turn tests into outside acceptance.

## Source, device, account and human gates

| Gate | Ready | Needed |
| --- | --- | --- |
| Desktop source | Required-source preflight and existing integration branches | Actual prim-sim / PrimSimCore repository or checkout, remote, commit and license. Never use a stub to make the build pass. |
| Primboard Mac release | MAC-RELEASE.md and safe candidate/notarization tooling; PR #5 macOS CI | Run that repository work order on the authorized Mac with its existing Developer ID. Retain signing/notary/Gatekeeper and installed existing-store, Touch ID/TCC and app/CLI results. Keep keys/private records out of public issues. |
| Native durability | Encrypted journal and controlled abrupt-process tests; same-key backup | Real device/disk-exhaustion/physical power-loss and representative large-store tests, plus independent review. Same-key backup cannot recover a lost key. |
| Browsers accounts | Synthetic signed Apple identity/session tests and dry builds | Preview cookie domain and real Apple/login/gateway/container session, then observed production route and rollback acceptance. |
| Public production | Hub preview, pinned legacy API, exact assets and rollback target | Current old-site clients, separate Railway service mapping, named operator/cost/escalation ownership, then a reviewable cutover and rollback plan. |
| Private/licensing migration | Per-repository inventory and public selected baselines | Scoped private-history/consumer audit; explicit reuse authority where no license was observed; ownership decision for private company products. |
| Independent stewardship | Governance, contribution and security documents | Actual role acceptance, private reporting/escalation, independent technical/domain review and an outside maintainer exercising the records. |

The Mac work is already specified in the product work order. Cloudflare does not provide a local Mac executor. No additional Mac installation is needed to use the public Hub's local/offline authoring.

## Remaining implementation

These items are not all blocked on the user. Continue in bounded branches with their own source and acceptance evidence:

- Publishing/resolution: authenticated publishers, aliases, namespace transfers and automatic approved remote refresh; real external/private-source publisher acceptance. Installed local source publication, dependency/cycle policy, deprecation/withdrawal and offline restore are implemented with evidence in the September 9 distribution record.
- Reference cases and composition: Receipt, Contract, Project and System alongside Person/Decision; identity, correction, context and cross-pack authority semantics that preserve real legacy meanings.
- Research/ingestion: challenge/review lifecycle, extraction provenance, recursive artifact budgets and changed/revoked/deleted source handling; useful life-domain diagnostics.
- Legacy migrations: safe readers, explicit semantic loss reports, sanitized positive/negative fixtures and tool/media separation. A preserved specification does not migrate its current consumers.
- Security/operations: scoped delegation, revocation and bounded work; actionable monitoring, stable maintenance and restore/exit exercises.
- Adoption: maintainable publisher/user instructions, localization and outside participation. Consent-based popularity must not be fabricated from test traffic.

Requirement IDs, acceptance, dependencies and evidence stages remain authoritative in `plan.json`. This handoff is not another ledger.
