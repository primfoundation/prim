# Prim Foundation repository reorganization

Status: proposed migration map, September 6, 2026. No repository is archived, renamed, deleted, or force-moved by this document.

## Goal

Organize repositories by **independent product/release responsibility**, not by Prim type, route, or temporary implementation experiment.

Target active top-level repositories should be few, durable, and understandable to a new maintainer without chat history.

## Current observed organization

Active repositories currently include:

- `primfoundation/prim`
- `primfoundation/prim-web`
- `primfoundation/prim-registry`
- `primfoundation/prim.workbook`
- `primfoundation/prims-desktop`
- `primfoundation/prims-browsers`
- `primfoundation/browsers-prims-sh`
- `primfoundation/logins-prims-sh`
- `primfoundation/prims-paste-desktop`
- `primfoundation/.github`

The current shape mixes five different concepts:

1. category/standards work;
2. individual profile experiments;
3. Foundation public cloud infrastructure;
4. end-user products;
5. route-specific deployment repositories.

That makes repo names leak historical implementation decisions into the architecture.

## Target model

### 1. `primfoundation/prim` — standards and definition source

Keep.

Owns:

- category specification and vocabulary;
- Foundation-maintained profile packages under `profiles/*`;
- conformance fixtures and compatibility baselines;
- profile publication contract;
- profile SDK contracts/reference tooling that must remain useful without the hosted Foundation;
- Foundation program/roadmap and normative architectural decisions until governance chooses another home.

Does **not** own:

- production website deployment;
- public runtime state;
- user accounts;
- popularity database;
- user Prim instances;
- a repository per profile.

Migration:

- move `prim.workbook` profile semantics/examples/tests into `prim/profiles/workbook` after compatibility inventory;
- preserve old repository history and publish a migration pointer before archive;
- Research, Person, Decision and future Foundation profiles coexist here without requiring repos.

### 2. `primfoundation/prims-hub` — public Foundation platform at `prims.sh`

Preferred target: preserve `prim-web` history by renaming/reworking it into `prims-hub` rather than creating yet another unrelated website repository, if GitHub/domain migration checks make that safe.

Owns:

- `prims.sh` website and docs presentation;
- profile catalog/index projection;
- public API;
- public remote MCP;
- publisher pages and later publisher/admin UI;
- popularity/ranking service;
- Cloudflare Worker/Static Asset config;
- D1 migrations, R2/Queue bindings, deployment runbooks;
- Hub-level audit/moderation.

Does **not** own:

- normative definition semantics;
- end-user Prim data;
- desktop/browser product internals;
- Foundation profile source as mutable database records.

Suggested monorepo shape:

```text
prims-hub/
  apps/
    public/            # Worker + Static Assets: web/API/MCP
    jobs/              # later: queues/schedules only
  packages/
    contracts/
    library/
    ranking/
    ui/
    testing/
  migrations/
  docs/
    architecture/
    operations/
  .cloudflare/
    manifest.json
  .github/workflows/
  wrangler.jsonc       # or per-app configs
```

Migration sources:

- `prim-web` → website/history/base repository;
- `prim-registry` → registry compatibility/API behavior;
- hosted runtime pieces from `prim/services/library` → shared Hub library/MCP implementation, while standards/contracts stay portable;
- public ranking implementation from current Library alpha.

### 3. `primfoundation/prims-desktop` — desktop host product

Keep independent.

Its build/signing/release lifecycle is materially different from a Cloudflare service. It consumes `prim` standards and Hub discovery but must remain useful offline.

### 4. `primfoundation/prims-browsers` — browser sandbox product

Keep, but absorb its cloud door infrastructure.

Move/merge:

- `browsers-prims-sh` → `prims-browsers/apps/gateway` or `cloud/gateway`;
- `logins-prims-sh` → `prims-browsers/apps/login` or `cloud/login` if that login remains product-specific.

Reason: those Workers exist solely to operate Prims Browsers; route-specific repositories create deployment sprawl and duplicate assets/session code.

Important boundary: do not reuse the Browsers shared login cookie as Foundation publisher/admin identity. Product identity and Foundation publishing authority are distinct.

After verified migration and DNS/deploy cutover, archive the old route repos with explicit successor links. Preserve their Git histories and release evidence.

### 5. `primfoundation/prims-paste-desktop` — encrypted paste/sticky product

Keep separate for now.

It has its own signed macOS application, encrypted local store, UX and release cycle. A future desktop-suite monorepo could be evaluated, but repository count alone is not a reason to merge independent products.

### 6. `primfoundation/.github` — organization defaults

Keep.

Expand carefully to own only organization-wide defaults:

- profile README;
- contribution/security/code-of-conduct defaults;
- issue/PR templates;
- shared reusable workflows where true organization-wide behavior exists.

Do not hide product-specific deployment logic here.

## Repositories to consolidate/archive after cutover

### `prim-registry`

Target: merge runtime contract and compatibility behavior into `prims-hub`.

Keep `registry.prims.sh` as a compatibility route during/after cutover if useful, but not as a reason for a permanent separate repository.

Before archive:

- inventory all clients of current endpoints;
- preserve HTTP semantics/redirects needed for compatibility;
- migrate tests;
- retain old release/config evidence;
- README points to successor and last supported commit.

### `prim.workbook`

Target: Foundation profile package under `prim/profiles/workbook`.

Before archive:

- identify every type/kind currently represented by the repo;
- preserve examples/validators/migrations;
- update registry/profile source metadata without changing semantic identity merely because files moved;
- test old consumers.

### `browsers-prims-sh`

Target: `prims-browsers` product monorepo.

### `logins-prims-sh`

Target: `prims-browsers` product monorepo unless its identity system is intentionally broadened into a Foundation-wide product later. Do not broaden it accidentally during consolidation.

## `prim-web` decision

Preferred approach:

1. audit repository for secrets, private-only assets, obsolete demos and deployment assumptions;
2. preserve useful public history;
3. rename `prim-web` to `prims-hub` (or equivalent durable name) if repository rename is operationally safe;
4. replace Railway/Pages deployment with Cloudflare Workers + Static Assets;
5. add platform apps/packages incrementally;
6. close/supersede the old Cloudflare Pages PR once the new Worker migration is reviewable.

Alternative if the repo is too contaminated by historical experiments: create a new `prims-hub` repository, import website history with an explicit subtree/history strategy, and archive `prim-web`. Do not copy files without preserving provenance.

## Why not one giant Foundation monorepo?

The standards library and public Hub should not be forced into the same deployment lifecycle as signed macOS apps, browser containers, and other products.

The desired unit of consolidation is **independent product responsibility**, not "fewest possible repos." A repo is justified when it has a materially different release/security/runtime boundary.

Therefore:

- many profiles in one standards repo: yes;
- multiple routes of one cloud Hub in one platform repo: yes;
- product-specific browser login/gateway with the browser product: yes;
- desktop and cloud Hub in one repo merely to reduce count: no.

## Target organization after migration

Likely active set:

```text
primfoundation/
  .github
  prim
  prims-hub
  prims-desktop
  prims-browsers
  prims-paste-desktop
```

Potential future products earn repositories by independent lifecycle, not by being a Prim type.

Archived compatibility/history repos remain discoverable with successor notices rather than being deleted.

## Migration rules

Every repository consolidation follows these rules:

1. inventory consumers, deployments, domains, secrets **names**, branches, open PRs and release evidence;
2. preserve source history or document exact imported commit lineage;
3. move tests before moving production traffic;
4. add successor compatibility paths;
5. verify real production behavior;
6. update all docs/links;
7. freeze old repo;
8. archive only after rollback window and real-use verification;
9. never force-push or delete history as cleanup.

Repo movement does not change profile identity.

## Relationship to AIC Hub

Borrow these patterns:

- monorepo around one control-plane product;
- explicit app/package boundaries;
- shared validated contracts;
- machine-readable Hub manifest;
- architecture docs that state ownership boundaries;
- one deploy model for related services;
- catalog + MCP as two surfaces over the same underlying control plane;
- fail-closed production readiness and auditable deployment evidence.

Do not copy AIC Hub's enterprise identity/data model: Prim Foundation's public library is anonymous-read-first, decentralized, and must not absorb user records.

## Immediate execution order

1. complete current Library/MCP PR review evidence;
2. inventory `prim-web`, `prim-registry`, route repos and current Cloudflare domains/bindings;
3. decide whether `prim-web` is safe to rename into `prims-hub`;
4. create Hub monorepo skeleton and Worker Static Assets deployment in preview only;
5. move catalog/MCP into Hub behind identical conformance tests;
6. migrate canonical website content/routes;
7. cut `prims.sh` and `mcp.prims.sh` to the unified Worker;
8. fold registry compatibility route;
9. then consolidate profile/product repos one at a time with evidence.
