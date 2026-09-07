# Library security boundary

Public MCP inputs contain profile IDs, versions, resource names, and search
terms—not private instance contents, filesystem roots, arbitrary URLs, imports,
votes or credentials. Schema execution and record creation stay local. Public
outputs are from an intentionally compiled read-only definition snapshot.
Definition text is untrusted data, never a source of host-level instructions.

Transport uses the official SDK; no home-grown JSON-RPC dispatcher. It supports
both current and legacy protocol modes. Host allowlists, Origin checks, request
body limits, stateless handling and resource pagination apply. Stdio logs never
write protocol noise to stdout. Application access logging and SDK telemetry
export are disabled by default. A host/proxy may have its own logging policy.
Search terms can still disclose information if a caller includes it: users and
agents must query public concepts rather than insert private facts.

Definition snapshots are bounded and hashed, including declared text resources.
Hashes establish integrity relative to a chosen snapshot, NOT publisher identity.
The build source and installed software must be trusted/reviewed by their operator.
No input profile executable or external schema reference runs. Arbitrary regex
schemas are disabled. JSON size/depth and array limits apply. This is not a
sandbox for hostile local code or an independent safety audit of dependencies.

Local creation assumes a trusted non-mutating parent directory. It rejects
symlinks and existing destinations, stages writes and then renames. This is not
a hardened descriptor-relative defense against a concurrent filesystem attacker,
and it does not provide full distributed concurrency or crash-consistency proof.
Unknown JSON fields survive; binary evidence is not automatically copied by this
creation command. Use the ORF preservation tool for its separately documented
legacy byte/layout transport, not this native scaffold.

Signed popularity events enter through an offline operator command. Public MCP
clients cannot vote or provide a count. Issuer secrets belong only to trusted
collection services that verify identity/consent and rate-limit issuance. Subject
HMACs and replay IDs remain private. Adoption is deduplicated; stars can be undone;
forgetting removes the actor's contributions; aggregate windows use complete UTC
days. Processed-event and daily-adoption details are pruned after 90 days during
ingestion; active star state persists until unstar/forget. Operators must also
manage backups, DB file permissions and tombstone retention.

Minimum cohort suppression is not differential privacy; identity federation,
Sybil resistance, anomaly review, rate limits for actual collectors, scoring
appeals and independent review remain open. No collection is activated in the
shipped empty rankings snapshot. Do not seed it with test events.

Public deployment requires explicit Foundation ownership, TLS/edge quotas,
monitoring, rollback, pinned release provenance and an incident contact. No
existing personal or employer workload is modified by this implementation.
