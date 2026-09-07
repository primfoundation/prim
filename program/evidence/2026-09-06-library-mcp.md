# Foundation Library MCP implementation — September 6, 2026

PR #7, branch `codex/foundation-library-mcp`, continues #6 without changing main.
The 17-workstream program retains all 70 existing IDs and adds nine explicit
MCP/publication/ranking/deployment/adoption requirements (79 total). Seven
milestones and every previous acceptance gate remain. No scope is silently closed.

## Actual implementation

Official MCP Python SDK 2.1.1; six public read-only tools over stdio/Streamable
HTTP, definition resources and an authoring prompt. Exact versions and complete
resource digests are returned. Human HTML, JSON routes and MCP use one library.
No public tool accepts private records, filesystem paths, arbitrary URLs, votes
or executable plugins. Local CLI creates/validates experimental Research,
Person and Decision from generic schema/template/rules; outputs carry definition
locks. Empty research stays draft. Private record data never needs to visit the
Foundation. Legacy ORF files and the old runtime/registry remain untouched.

Popularity and momentum use an operator-only signed-signal engine, SQLite
pseudonyms, replay/daily adoption deduplication, reversible stars, deletion,
small-cohort suppression and stale-snapshot handling. The distributed ranking
snapshot is empty. Public identity/consent collection and anti-Sybil review are
not activated or claimed complete.

## Build inputs and transfer provenance

Read-only acquisition run 34062910196 exported exact public source at
65b956b03c5eee4b309bbc61df2a57e413b34fb0 and binary Python dependencies.
Artifact 9998029478 SHA-256:
`e929d2c7bb182105833e09f20f4a6d7debb0f76e23c6c09bf87d3514c433151d`.
The artifact and its contained checksum manifest were verified before use.
It contains no credentials/private records. Dependency resolution is retained
in services/library/constraints.txt. The temporary acquisition workflow is not
part of the final service or an unattended execution mechanism.

## Verification record

`library-tests.json` records actual local unit/protocol/inherited regression and
clean installed-wheel results. The complete report and install artifacts are
retained with the build. Protocol tests exercise both current and legacy SDK
client modes over real stdio and loopback HTTP, plus in-process resources and
prompts. HTTP includes host/origin/body rejection, JSON discovery and a human
catalog. Native record tests cover required evidence links, references,
contradiction, draft vs completion and recorded (not authenticated) review.

CI independently repeats checks, builds a wheel, installs it into a clean venv,
and runs outside the checkout. A workflow definition is not a passing result;
observe PR #7's exact head and run before claiming remote success. Evidence added
after a tested commit is a separate checkpoint. Docker build and actual public
TLS deployment are not inferred from local HTTP or wheel installation.

## Limits and next operations

Alpha package; no PyPI publication, public Foundation URL, production activation,
independent security review, authenticated public voting, real-user onboarding,
or universal client compatibility is claimed. A lookup hash is not publisher
authentication. Signing a signal is not proof of a unique person. Cohort thresholds
are not differential privacy. An operator must approve any publicly served
custom definition source and its content. See services/library/SECURITY.md.

Next: confirm the Foundation hosting owner/budget and deploy a pinned reviewed
service; complete authenticated opt-in adoption signals and external publishing;
continue native Research lifecycle and loss-aware ORF semantic migration. Neither
MCP nor three schemas discharge the much larger Foundation roadmap.
