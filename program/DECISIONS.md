# Decision register

## D001 — Durable record and evidence gates

Status: selected within the authorized implementation.

Use `primfoundation/prim` as the intended durable home. The plan is machine-readable; the roadmap is generated. PRs reference requirement IDs. JSON/Markdown are the bootstrap record, not a new Project Prim certification. The initial GitHub authorization blocker is resolved; the preserved local artifacts remain the historical baseline.

## D002 — Publishable package, not repository

Status: accepted direction; syntax is experimental.

A profile can be hosted independently. Identity, publisher namespace, version, and source location are distinct. For this slice use `PROFILE.md` with safe YAML metadata and a Markdown body, with relative resource pointers and progressively loaded documentation. Discovery is local-only, opt-in by selected source root, and never executes code. The old registry is unchanged.

Prototype identity spelling is `namespace/name`; it is not tied to GitHub ownership and does not authenticate a publisher. Lifecycle, visibility, publisher verification, and conformance are different dimensions. The manifest's maturity is self-declared. No remote installer, signature verifier, or validator runner is implied.

## D003 — Research first, ORF preserved

Status: accepted direction; detailed semantics are in development.

Separate enduring investigations from producer-specific orchestration. Preserve questions, evidence, claims, uncertainty, counterevidence, history, review, and authorization provenance. A machine check must not manufacture confirmation.

Do not relabel ORF bytes as Research and claim interoperability. Record the baseline; collect unmodified fixtures and differential tests before an adapter ships. Historical aliases are descriptive metadata until an explicit, versioned resolver exists. Profile and encoding versions become independently managed in vNext, without retroactively changing ORF's rules.

## D004 — Additive, reversible bootstrap

Status: selected implementation safeguard; narrow test-only exception in D006/D007.

No changes to existing category, registry, SDK runtime, ORF, or person files. D006/D007 permit the documented changes to one existing SDK test file after full-checkout CI exposed two baseline test problems. No production deployment, package publication, tag movement, repository archive, secret transfer, or paid unattended work. Preserve the existing `sdk-python` and `prims/zeroshot-connector` branches. Their existence is not proof of active work.

## D005 — Reference tooling, not premature platform commitment

Status: selected, reversible implementation choice.

The first local discovery/compiler uses Python and PyYAML; the program checker uses the Python standard library. No custom partial YAML parser is added. This does not select the production runtime, supersede the TypeScript SDK, or overwrite the existing Python branch. Integration into production SDK/CLI surfaces is a separately tested obligation. Discovery reports manifest checks separately from unperformed instance validation, security review, and publisher authentication.

## D006 — Correct stale host expectations without changing runtime

Status: implemented; full-checkout CI passed, independent review remains open.

The existing registry and SDK correctly include wildcard Mac/web hosts. Two old test expectations omitted them. Preserve strict equality and editor precedence, include the existing hosts, and add positive/negative host-filter checks. Rationale and failed-run evidence: [publication evidence](evidence/2026-09-06-publication.md).

## D007 — Make SDK contract fixtures self-contained

Status: implemented; full-checkout CI passed, independent review remains open.

Always run book contract assertions on a local synthetic fixture; keep the optional sibling integration when available, report absence explicitly, and fail malformed available examples. Do not make a private sibling checkout a prerequisite for testing the public SDK. Rationale: [fixture evidence](evidence/2026-09-06-sdk-fixture.md). Passing result for both corrections: [CI summary](evidence/ci-34057807656.json).

## D008 — Preserve and characterize the exact ORF baseline

Status: implemented on the Research compatibility branch; review remains open.

Keep all 15 upstream source files, license and examples unchanged at the pinned
ORF commit. Verify sizes, SHA-256 and Git blob IDs before loading the reviewed
local oracle. Run its actual CLI and self-tests, then retain counterexamples
showing where a legacy pass differs from completeness or factual correctness.
Do not fix old semantics inside the preserved baseline. Source acquisition used
read-only CI with public, pinned commits; no tokens entered the source artifacts.

## D009 — Byte preservation is not semantic migration

Status: selected, implemented reference transport; not a ratified Prim encoding.

Provide an explicitly named versioned preservation envelope for file bytes,
relative paths and empty directories. Document lost OS/archive metadata. Restore
to new destinations only; never overwrite originals. Derived Research previews
and browser views cite hashes and retain original metadata; they are not a second
authority and do not turn citations into evidentiary support. RES-001 stays in
progress until the target Research migration and independent review are proven.

## D010 — Local compatibility before remote execution

Status: selected, scoped implementation boundary.

Directory packs and the preservation envelope are supported. No remote fetch,
arbitrary validator import, ZIP/TAR ingestion, live agent runtime, cloud service
or package release is added. Unrecognized versions and oracle exceptions cannot
produce a passed profile result. Broader trust boundaries and limitations are
recorded in THREAT-MODEL.md. Production SDK integration is still separate work.

## D011 — Preserve whole-life direction while implementing Research

Status: scope clarification, not new schema proliferation.

The larger mission remains overlapping Worlds/contexts, not one folder taxonomy.
Life diagnostics must distinguish Coverage, Fidelity and Operability and must not
confuse silence or artifact count with completeness. The current domain list is
provisional; reconcile it against the original discovery scaffold under PRG-004
and LIFE-001 rather than pretending the scaffold is already exhausted. This slice
removes no workstreams, requirements, milestone gates or reference cases.

## Open decisions

| ID | Decision | Evidence needed |
| --- | --- | --- |
| D101 | Reconcile semantic substrate and category primitives | Research plus the six reference cases; small-envelope proposal; compatibility analysis. |
| D102 | Permanent IDs, publisher verification, transfer, and aliases | Collision, ownership-transfer, source-move, and offline-resolution cases. |
| D103 | Research vNext encoding, evidence policies, and mappings | Real investigations; contradiction, review, and freshness tests; relevant primary standards. |
| D104 | Governance, legal/IP/trademark policies, and commercial boundary | Explicit human decisions and appropriate professional review; no assumed legal status. |
| D105 | Hosting, budget, free-core/service boundary, and operations | Actual infrastructure inventory, cost/recovery/abuse model, authorized budget. |
| D106 | Stable releases and independent conformance | Two independent implementations with version-specific results. |
| D107 | Public/private diagnostics and adoption metrics | Threat model, privacy review, explicit collection policy. |

A selected choice is reversible engineering within this implementation, not a claim the founder ratified every field. Superseding decisions retain history and state migration consequences. Publishing permission is an operational concern, not a reason to weaken architectural gates.

## D012 — Foundation MCP distribution is a first-class delivery path

Status: founder requested September 6; implemented alpha, independent review open.

Add an installable stdio/Streamable HTTP service backed by the same versioned
library as human/JSON discovery. Public tools retrieve definitions, not private
records. Agents obtain schemas and blank templates and create/validate locally.
One generic kit contract works for multiple profiles. The server is neither an
agent nor a hosted store for personal work. Existing TypeScript interfaces and
legacy ORF interpretation are not silently replaced.

## D013 — Popularity is consented adoption, not truth

Status: selected alpha scoring policy; public signal collection not activated.

Separate Popular (longer-term stars/adoption) and Trending (recent capped momentum).
Search relevance still filters results. Approved collector services sign events;
end-user client assertions alone cannot inflate counts. Deduplicate adoption,
retain star/unstar and deletion semantics, suppress small cohorts, neutralize
stale snapshots, and start with genuine no-data rather than seeded popularity.
Trusted issuers still need identity/consent verification and anti-Sybil review.
Read requests do not automatically become votes. Scoring and public collection
can evolve through explicit versioned policies; neither implies security quality.

## D014 — Small native drafts, not an unratified universal model

Status: experimental Research, Person and Decision creation demonstrated.

Research's development model separates claims, sources, evidence relationships,
activities, workflow/outcome and recorded review. The same declaration-driven
schema/template mechanism handles Person and Decision. Unknown JSON fields are
preserved. This proves an authoring path, not a stable universal substrate,
authenticated review, full lifecycle, or semantic ORF migration. Four remaining
non-research reference cases and independent implementations remain obligations.

## D015 — Hosting is a named ownership decision

Status: public deployment gate open; portable software proceeds independently.

Build and test a remotely hostable package and container recipe. Do not invent a
live endpoint or deploy Foundation infrastructure into an unrelated account just
because credentials exist. A read inventory did not establish a Foundation-owned
hosting target. Record the ownership/budget/TLS/operations gate as OPS-005; no
private account identifiers or credentials belong in this public record.


## D016 — Authorized preview delivery and source stabilization

Status: executed September 8, 2026; production ownership gate retained.

Subsequent explicit founder instructions authorized continued shipping through the
selected Clawdflare connection. D015's unknown-target condition was resolved for
the existing isolated Hub preview, whose deployment and recovery evidence is
retained in `evidence/2026-09-08-release.json`. This is not a production domain
cutover or proof of Foundation legal ownership, operating budget or independent
acceptance. Those parts of OPS-001/OPS-005 remain open.

The Hub workbench ships as a development alpha using the same immutable profile
versions. Primboard's versioned encrypted index and same-key backup/recovery are
merged after Mac CI; no existing private store was migrated by this work session.
Signed device acceptance, a multi-file crash journal and lost-key recovery remain
open. The legacy Railway service mapping failure is retained as an operational
finding, not represented as a successful production deployment.

## D017 — Recover complete notebook operations before admitting access

Status: implementation and macOS software-fault tests complete; broader G3 gates open.

Primboard publishes an authenticated encrypted redo record before changing any
referenced payload/index files. That publication is the commit point. All updated
store readers/writers finish valid pending replay under the existing process lock
before proceeding; malformed records and unexpected file state are preserved and
block access. A save error after publication can mean a committed operation, so
callers reload/reconcile rather than blindly repeat an add. Changes retain the
existing bundle, CLI, store and Keychain identities and current index encoding.

This supersedes D016's journal-not-implemented observation only. Both app and CLI
must be journal-aware. The journal requires the same existing key and does not
provide key-loss recovery, arbitrary-corruption repair or authorization to use
private records. Physical power loss, device/filesystem failure matrices,
large-store latency, independent review and signed installed acceptance remain
separate obligations. The shared cloud Apple release system is not activated.

Evidence and exact scope: `evidence/2026-09-08-primboard-journal.json`.
