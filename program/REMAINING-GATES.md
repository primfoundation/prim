# Remaining delivery gates

The original Foundation scope remains intact. The user's new 95% target is sequenced in [DELIVERY-95.md](DELIVERY-95.md); it does not remove unfinished requirements or turn tests into outside acceptance. The September 11 Fleet audit replaces the earlier lack-of-Mac-access assumption.

## Source, device, account and human gates

| Gate | Ready | Needed |
| --- | --- | --- |
| Desktop source | Private recovery copies verified; recovered PrimSimCore and clean Desktop builds pass | Recover source lineage/reuse authority (no Git/root license observed), resolve the legacy host suite (20 tests run with 27 assertion failures) and reconcile integration branches. Never use a stub to make the build pass. |
| Primboard Mac release | Private source recovery on both Macs; signed candidate accepted by Apple, stapled and Gatekeeper-verified; verified prior app/store backup and rollback | Existing-store attempt failed before migration: installed development notebook has video/new metadata absent from clean main. Reconcile those semantics before reinstalling; finish native complete-pack storage, Touch ID/TCC and app/CLI acceptance. Original app/CLI restored; notebook bytes unchanged. |
| Desktop installation identity | Two installed copies observed with different bundle IDs | Map launch/file association and permission principal before choosing a signed candidate. Do not delete either installation or rename runtime identities as cleanup. |
| Native durability | Encrypted journal and controlled abrupt-process tests; same-key backup | Real device/disk-exhaustion/physical power-loss and representative large-store tests, plus independent review. Same-key backup cannot recover a lost key. |
| Browsers accounts | Synthetic signed Apple identity/session tests and dry builds | Preview cookie domain and real Apple/login/gateway/container session, then observed production route and rollback acceptance. |
| Public production | Hub preview, pinned legacy API, exact assets and rollback target | Current old-site clients, separate Railway service mapping, named operator/cost/escalation ownership, then a reviewable cutover and rollback plan. |
| Private/licensing migration | Per-repository inventory and public selected baselines | Scoped private-history/consumer audit; explicit reuse authority where no license was observed; ownership decision for private company products. |
| Independent stewardship | Governance, contribution and security documents | Actual role acceptance, private reporting/escalation, independent technical/domain review and an outside maintainer exercising the records. |

The Mac work is already specified in the product work order and can now be executed through the selected Fleet connection. No additional general-purpose Mac executor installation is indicated. Actual OS consent, keychain interaction or source-owner decisions may still require a person at the specific gate. Prepare concrete candidates and evidence before asking.

## Remaining implementation

Library/SDK complete-pack transfer and the live Hub attachment-preserving editor are shipped. Native complete-pack storage is still missing; record-only import must not discard attachments.

These items are not all blocked on the user. Continue in bounded branches with their own source and acceptance evidence:

- Publishing/resolution: authenticated publishers, aliases, namespace transfers and automatic approved remote refresh; real external/private-source publisher acceptance. Installed local source publication, dependency/cycle policy, deprecation/withdrawal and offline restore are implemented with evidence in the September 9 distribution record.
- Reference cases and composition: Receipt, Contract, Project and System alongside Person/Decision; identity, correction, context and cross-pack authority semantics that preserve real legacy meanings.
- Research/ingestion: challenge/review lifecycle, authenticated remote extraction and permission enforcement, recursive/encrypted/media parsing and changed/revoked/deleted source handling; useful life-domain diagnostics. Installed bounded local capture, byte-preserved originals, recorded provenance and retry/folder verification now have September 9 evidence.
- Legacy migrations: safe readers, explicit semantic loss reports, sanitized positive/negative fixtures and tool/media separation. A preserved specification does not migrate its current consumers.
- Security/operations: scoped delegation, revocation and bounded work; actionable monitoring, stable maintenance and restore/exit exercises.
- Adoption: maintainable publisher/user instructions, localization and outside participation. Consent-based popularity must not be fabricated from test traffic.

Requirement IDs, acceptance, dependencies and evidence stages remain authoritative in `plan.json`. This handoff is not another ledger.
