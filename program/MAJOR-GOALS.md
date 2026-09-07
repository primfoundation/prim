# Prim Foundation major goals

Status: execution contract. These are outcome goals, not activity buckets. A goal is not complete because code exists or a PR is open; its acceptance evidence must exist.

## G1 — One canonical standards system

Finish when `prim` can publish Foundation and external profile packages without repository-dependent identity; version/publisher/distribution semantics are explicit; conformance fixtures and legacy compatibility are retained; profile-only incubators can retire without breaking old files.

Evidence required: implementation, two-reader interoperability, migration fixtures, review, published package/catalog evidence.

## G2 — One coherent public Foundation Hub

Finish when `prims.sh` website, catalog, API, remote MCP, definition detail and compatibility routes run from one Cloudflare-native control plane and return identical pinned definition identities. Preview, production, health, rollback, monitoring, accessibility/mobile and a real external MCP client must pass.

The Hub distributes definitions; it is not a cloud store for private user Prims.

## G3 — Primboard is a trustworthy first-class product

Finish when the product/repo is coherently Primboard while compatibility-sensitive runtime identities continue to open existing stores; sensitive index metadata is encrypted or demonstrably nonsensitive; concurrent app/CLI writes and crash recovery are safe; backups/migrations are tested; product backlog fixtures no longer seed normal user boards; generic `Convert to Prim…` works locally using pinned Library definitions; signed-Mac/TCC acceptance passes.

## G4 — Prims Browsers is one product

Finish when browser runtime, cloud gateway and login live under one product boundary with shared contracts, no duplicated auth/session/brand implementation, and existing `login.prims.sh` / `browsers.prims.sh` behavior passes end-to-end. Old route repos become read-only history only after rollback and real-use evidence.

## G5 — Prims Desktop is the generic offline host

Finish when a newly published profile can be discovered/opened/inspected through the generic profile/tool contract without shipping bespoke Swift code unless OS-native integration is genuinely required. Existing Mac-only connector/FDA/XPC/person/debug work is reconciled and proven rather than discarded. File authority remains the Prim itself.

## G6 — Legacy Prim invention is migrated without erasure

Finish when every discovered Eidos `prim.*` incubator is classified and either: imported as a profile with source provenance; split into definition plus justified tool/product; retained privately with an explicit reason; or archived as compatibility history. No useful invention, consumer, private-data concern or release lineage is lost.

## G7 — The Foundation can outlive its current maintainers

Finish when repository lifecycle, contribution/governance, release, dependency, security response, backup/restore, cost ownership, operational manifests, public compatibility promises and archive gates are documented and exercised. A new maintainer can build, test, deploy, roll back and extend the system from repository records without reconstructing private chats.

## Execution rule

Work these goals in parallel where safe. Stop only at a genuine human/credential/legal/cost/real-device gate. Record that gate instead of converting it into fake completion. No repo is renamed/archived, no production DNS is changed, and no private record is moved merely to make the topology look clean.
