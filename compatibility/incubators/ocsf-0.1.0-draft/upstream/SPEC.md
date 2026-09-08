# OCSF v0.1.0-draft — Open Corporate Structure Format

**An additive profile of OKF v0.2.**  
Every OCSF document preserves OKF provenance and trust.  
OKF renderers may ignore OCSF fields and still display the documents.

**Product intention (load-bearing):** see [INTENTION.md](INTENTION.md).

In one line: OCSF packages the legal-entity graph, ownership & control interests, capital instruments, governance rights, and cash-flow rules of a corporate group as a self-contained, evidence-backed, agent-validatable pack.

```
OKF  — knowledge and trust
EMF  — human intent and durable memory
ORF  — research / investigation packs
OPF  — product graph
ODFW — spreadsheet → bronze proof
OPFF — personal finance packs
OMF  — meeting occurrences
OCSF — corporate structure & capital   (this profile)
```

OCSF composes with these formats; it does not merge them.  
Human intent remains EMF. Research remains ORF. Product surfaces remain OPF. Finance ledgers remain OPFF. OCSF owns the group architecture, claim priority, and risk boundaries.

---

## 1. Pack

```
ocsf-pack/
  index.md                 # required face (type: group or legal_entity)
  log.md                   # append-only timeline
  structure.json           # canonical graph (entities + relationships + events) — semantic authority
  entities/                # optional human-readable projections
  instruments/
  relationships/
  events/
  governance/
  cash_rules/
  evidence/                # native proof artifacts (PDFs, hashes, etc.)
  docs.json                # optional okflify presentation settings
```

`structure.json` is the only semantic authority for the graph.  
Markdown files, folder names, and links do not add or change entities or relationships.

Minimal face frontmatter (index.md):

```yaml
okf_version: "0.2"
ocsf_version: "0.1.0"
profile: ocsf
type: group                # or legal_entity
title: Eidos Group
status: active
```

---

## 2. Core kinds (nodes)

| Kind | Purpose |
|------|---------|
| `legal_entity` | Corporation, LLC, SPV, HoldCo, OpCo, AssetCo, etc. |
| `natural_person` | Individual |
| `fund` / `trust` / `arrangement` | Collective or special vehicles |
| `share_class` | Common, Preferred Series A, etc. |
| `equity_instrument` | Specific shareholding or option grant |
| `debt_instrument` | External loan, bond, note |
| `intercompany_loan` | Parent ↔ subsidiary note |
| `guarantee` | Guarantee or security interest |
| `option` / `warrant` / `convertible` | Contingent equity |
| `agreement` | IP license, services, cost-sharing |
| `approval` / `board_resolution` | Governance act |

Every entity has a stable `id`, `type`, `title`, lifecycle `status`, and `provenance`.

---

## 3. Typed relationships (edges)

Relationships are first-class records with stable IDs. Meaning lives in their typed direction.

Common types:

- `owns` (percentage, voting_rights, economic_rights, effective_from, effective_to)
- `issues` / `holds`
- `guarantees` / `subordinated_to`
- `licenses_ip_to` / `provides_services_to`
- `appoints_board` / `has_reserved_matter_rights`
- `has_distribution_right` (with constraints)
- `controls` (direct / indirect / ultimate)

Ownership percentages for a given class or entity **must** be consistent under validation (see §5).

---

## 4. Events

Canonical temporal events (issuance, transfer, conversion, amendment, distribution, board approval, incorporation, dissolution) live as first-class records so the graph can be reconstructed at any point in time.

---

## 5. Validation gates (draft — fail-closed)

| Rule | Level |
|------|--------|
| `okf_version: "0.2"` + `profile: ocsf` + valid `ocsf_version` | error |
| Ownership percentages for any share class / entity sum correctly (tolerance for treasury / authorized) | error |
| No ownership cycles unless explicitly justified and documented | error |
| Material claims (ownership > threshold, guarantees, intercompany terms) require evidence + content hash | error |
| Evidence trust tier visible; agent-only claims warned | warn / error under --strict |
| Temporal consistency (effective dates, supersedes) | error |
| Distribution / upstreaming assertions pass solvency + covenant gates | error |
| LEI / registration numbers unique within pack where present | error |
| Secret-shaped strings (PANs, live balances, tokens) | error |

Additional gates will be added as the format hardens.

---

## 6. Evidence & trust

Every material claim carries:

```yaml
provenance:
  by: human:daniel | agent:codex | job:...
  method: "board resolution 2026-08-01" | "stock purchase agreement"
  at: "2026-08-01"
verified:
  by: human:...
  at: ...
  method: direct | document_hash
stale_after: "2027-08-01"   # optional
evidence:
  - path: evidence/spa-2026-08-01.pdf
    content_hash: sha256:...
```

Trust ladder follows OKF v0.2: `human:` > `job:` > `agent:`.

---

## 7. Interoperability

- Prefer LEI as the stable external identity when available.
- Provide export helpers toward BODS statements for beneficial-ownership disclosure.
- Accept import of OCF (Open Cap Format) equity detail for single-issuer views.
- Compose with OPFF for personal-plane finance and OPF for product commitments.

---

## 8. Status

**v0.1.0-draft.**  
INTENTION and this SPEC skeleton exist.  
Validator, minimal fictional example, and structure.json schema are next.

---

## License

MIT — Eidos AGI
