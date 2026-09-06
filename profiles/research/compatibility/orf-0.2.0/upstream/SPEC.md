# ORF v0.2.0 — OKF Research Format

**An additive profile of [OKF v0.2](https://github.com/eidos-agi/okflify).** Every ORF document
is a valid OKF document. Renderers that know only OKF display it correctly and ignore the extra
keys; `okflify` needs no changes.

ORF is the OKF face for **investigations**: what we set out to learn, the approved plan, graded
findings, and what remains open. It is not capital diligence (deedee) and not durable org memory
(EMF). Squiddie and other research harnesses write ORF packs; they may *promote* findings into
EMF claims later.

If a requirement conflicts with OKF v0.2, **OKF wins for base structure**. ORF only adds
required frontmatter, pack layout conventions, and research gates.

```yaml
---
okf_version: "0.2"        # unchanged — ORF is a profile, not a fork
orf_version: "0.2.0"
type: Investigation       # pack face; findings use claim (or investigation)
title: "Goldfish memory myth — weeks not seconds"
profile: orf
question: "Do goldfish really have only a 3-second memory?"
status: done              # intake | planned | running | done
approval: go              # pending | go  — pack must not be "done" without go
brief:
  goal: "sanity-check a common claim before citing it"
  scope: "peer-reviewed or high-quality secondary sources; not pet-store folklore alone"
  audience: "internal research dogfood"
  success_looks_like: "graded findings with host-independent sources"
plan:
  k: 2
  sub_questions:
    - "What is the origin of the 3-second claim?"
    - "What do controlled studies measure for retention?"
  estimate: quick         # quick | standard | deep
verified:
  by: agent:squiddie
  at: 2026-08-03
  method: "ORF pack after interview + user go; arms Flash-0731"
  stale_after: 2026-11-01
---
```

---

## 1. Why ORF exists (measured failures)

Each addition exists because a failure was felt or measured — same discipline as EMF.

| Failure | Therefore |
|---------|-----------|
| Chat noise ("Hi") became a durable research pack | **Admission:** durable packs need a real `question` and `approval: go` |
| Fan-out without shared plan | **`plan.sub_questions`** (or equivalent) after interview |
| Confident citations without independence | **Evidence grades** + host count gate on CONFIRMED |
| Confusion with diligence packs | **No** capital `verdict` (WATCH/PASS/COMMIT) in ORF |
| Confusion with org memory | Agents **do not** author EMF `type: intent`; promote claims into EMF separately |
| Lost “what was the ask?” | **`question` + `brief`** on the face |

---

## 2. Relationship to OKF, EMF, and deedee

| Layer | Spec |
|-------|------|
| Bundle tree, reserved `index.md` / `log.md` | OKF |
| Concept = markdown + frontmatter, `type` required | OKF |
| `sources`, `generated`, `verified`, `status`, `stale_after` | OKF |
| Trust ladder `human:` > `job:` > `agent:` | OKF — **unchanged** |
| `altitude`, `type: intent`, `concerns`, `sensor` | **EMF** — optional on promoted docs only |
| `verdict`, clocks, economic claim tiers | **deedee** — out of scope for ORF |

```
OKF v0.2
├── EMF    — memory (intent / claims / altitude / concerns)
├── ODDF   — capital diligence (OKF Due Diligence Format; was “deedee”)
└── ORF    — research / investigation packs
```

**Compose, don't merge:** a finding may later gain `emf_version` when promoted to org memory.
The investigation face stays ORF.

---

## 3. Bundle unit and layout

**Unit of distribution: one investigation** (one approved research question / brief).

```
path/to/investigation/
  index.md                 # REQUIRED face (question → nutshell → answer)
  log.md                   # REQUIRED append-only timeline (OKF; no frontmatter required)
  findings/                # One file per graded finding (OKF concepts)
    *.md
  evidence/                # Optional extracts, PDFs, notes — no secrets
    …
  plan.md                  # Optional if plan lives fully in index frontmatter
  brief.md                 # Optional if brief lives fully in index frontmatter
  emf/                     # Optional: promoted EMF agent claims (never human intent by agent)
    index.md
    claims/
  research.json            # Optional machine sidecar (spend link, backends, session_id)
```

Producers MAY use `.research/<id>/` as the path (Squiddie default). Document the path in the
pack index when reseated.

---

## 4. Pack face (`index.md`) — required profile fields

In addition to OKF fields producers already use:

| Field | Required | Meaning |
|-------|----------|---------|
| `okf_version` | MUST | `"0.2"` |
| `orf_version` | MUST | `"0.2.0"` (this profile) |
| `type` | MUST | `Investigation` (preferred) or OKF `investigation` |
| `title` | MUST | Display title |
| `question` | MUST when `status` ∈ {planned, running, done} | Single governing research question |
| `status` | MUST | `intake` \| `planned` \| `running` \| `done` |
| `approval` | MUST when writing a durable pack past intake | `pending` \| `go` |
| `profile` | SHOULD | `orf` |
| `brief` | SHOULD when planned+ | goal, scope, audience, success_looks_like |
| `plan` | SHOULD when planned+ | k, sub_questions[], estimate |
| `verified` | MUST | OKF ladder; method how the pack was produced |

### Admission rules (conformance that bites)

1. A pack with `status: done` MUST have `approval: go`.
2. A pack with `status: done` MUST have non-empty `question`.
3. `approval: go` without a non-empty `question` is an error.
4. Producers MUST NOT set `status: done` on greets, empty chat, or missing brief when the
   runner supports interview mode — validators enforce 1–3; runners enforce the interview gate.

### Non-goals on the face

- `verdict: watch|pass|commit` — use deedee.
- `type: intent` authored by `agent:*` — use EMF; agents record human intent only as human tier.
- Softening OKF trust tiers.

---

## 5. Findings — evidence grades

Each file under `findings/` is an OKF concept. ORF adds:

```yaml
---
okf_version: "0.2"
orf_version: "0.2.0"
type: claim
title: "…"
evidence: CONFIRMED          # CONFIRMED | REASONED | UNVERIFIED
sub_question: "…"            # tentacle question
sources:
  - https://example.com/a
  - https://example.com/b
disconfirmation: "…"         # what was searched to disprove; required for CONFIRMED
verified:
  by: agent:squiddie
  at: 2026-08-03
  method: "fan-out arm; gate applied"
  stale_after: 2026-11-01
---
```

### Evidence rules

| Grade | Meaning | Gate |
|-------|---------|------|
| **CONFIRMED** | ≥2 **independent** sources (distinct hosts) agree; disconfirm search logged | If hosts &lt; 2 → **MUST** downgrade to REASONED (writer or reader) |
| **REASONED** | Source-backed but not dual-host confirmed, or partial | Honest middle |
| **UNVERIFIED** | Conflict, missing sources, or arm error | Must not be sold as confirmed |

**Independent hosts:** count registrable hostnames; `www.` stripped; same site ≠ two sources.

`disconfirmation` SHOULD be non-empty for CONFIRMED; empty is a **warn** (error if `--strict`).

---

## 6. Conformance

- Every ORF document MUST be a valid OKF v0.2 document (`okf_version: "0.2"`).
- `orf_version` MUST use `X.Y.Z`; `X.Y` MUST equal `okf_version`.
- ORF-only revisions increment `Z` (`0.2.1`, `0.2.2`, …). A new OKF line resets ORF to
  that line's `.0` release (OKF `0.3` → ORF `0.3.0`).
- Pack face MUST carry `orf_version` when claiming ORF conformance.
- `status: done` ⇒ `approval: go` and non-empty `question`.
- Finding `evidence: CONFIRMED` with &lt;2 distinct source hosts MUST be treated as REASONED
  (validator **error** if still labeled CONFIRMED).
- Agents MUST NOT author `type: intent`.
- Capital `verdict` is not required; if present, warn (wrong profile — use deedee).
- `log.md` has no frontmatter requirement (OKF append-only convention).

Validate:

```bash
python3 -m orf.validate <pack-or-file>...
python3 -m orf.validate --selftest
python3 -m orf.validate --strict examples/orf-minimal
```

---

## 7. Placement (not part of the document schema)

ORF is a **format**. It does not define a global research warehouse.

| Default | Reseat |
|---------|--------|
| `.research/<id>/` next to the work (e.g. Squiddie) | `docs/orf/`, ledger edition trees — declare in index |

**This repository** (`eidos-agi/orf`) ships **spec, validator, examples**. It is not the org research corpus. Squiddie and other harnesses are consumers that write packs next to their work.

---

## 8. Prior art

| | |
|--|--|
| **EMF** | Additive OKF profile pattern — dual version stamps, measured failures, biting conformance |
| **deedee** | OKF profile for capital decisions (AIC-313) |
| **okflify** | Renders OKF; ignores profile keys |
| **Squiddie** | Research harness that should produce ORF packs after interview + go |

---

## 9. Version

| | |
|--|--|
| Profile | ORF **0.2.0** |
| Base | OKF **0.2** |
| Status | Draft — dogfood with Squiddie |
