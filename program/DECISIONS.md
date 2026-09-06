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

Status: selected implementation safeguard.

No changes to existing category, registry, SDK, ORF, or person files. No production deployment, package publication, tag movement, repository archive, secret transfer, or paid unattended work. Preserve the existing `sdk-python` and `prims/zeroshot-connector` branches. Their existence is not proof of active work.

## D005 — Reference tooling, not premature platform commitment

Status: selected, reversible implementation choice.

The first local discovery/compiler uses Python and PyYAML; the program checker uses the Python standard library. No custom partial YAML parser is added. This does not select the production runtime, supersede the TypeScript SDK, or overwrite the existing Python branch. Integration into production SDK/CLI surfaces is a separately tested obligation. Discovery reports manifest checks separately from unperformed instance validation, security review, and publisher authentication.

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
