# Research Prim — development design brief

Status: discovery prototype; not a replacement for the ORF 0.2.0 specification.
Publication package version: 0.3.0-dev.1. No stable instance encoding is selected.

## Durable outcomes

An investigation preserves its governing question, purpose, scope, source
material, individually addressable claims, supporting and opposing evidence,
assumptions, unanswered questions, activities, revisions, and review decisions.
The report is a view; it must not become the only remaining research record.

An unfamiliar worker must distinguish direct observations, attributed source
claims, inference, estimates, and unresolved disagreement. Source identity,
retrieval time, evidence location, content integrity when available, lineage,
and reuse constraints belong in the record. Distinct websites alone do not
prove independent evidence. A hash establishes byte identity, not truth.

## Process and authority

Research can be produced by a human or any agent. A producer's interview,
fan-out count, backend choice, or approval dialogue is not a universal research
format requirement. Record meaningful activities and authorizations by reference.
A completion state is separate from review status, factual support, and freshness.
Human permission must have provenance; a writable `human:` label is not proof.

## Lifecycle cases required before stabilization

Continue an unfinished investigation; record contradiction without erasure;
correct a claim with an explanation; identify stale evidence; preserve previous
revisions; supersede or retract a conclusion; regenerate a report; distinguish
missing evidence from disproving evidence; share a redacted copy without
silently representing it as the complete original; survive an unavailable source.

## Legacy contract

The existing `eidos-agi/prim.orf` SPEC and validator remain authoritative for
historical ORF 0.2.0. Relevant observed blobs are recorded in
`program/BASELINE.md` at the repository root. No legacy bytes, commands, source
hosts gate, version rule, or admission rule are changed here. Future adapters
must preserve originals, describe information loss, and pass differential tests.
Adding `legacy_aliases: [orf]` is not such an adapter.

## Open gates

Claim/source/evidence identifiers and relationships; minimal interoperable
encoding; evidence-policy selection; revision semantics; authenticated review
receipts; category/grammar version compatibility; genuine legacy fixtures;
two independent readers/writers; and mappings to relevant provenance and
research-object standards remain open. Those obligations live in the program
ledger rather than being presented as implemented features.
