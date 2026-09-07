# prim.workbook — SPEC (v0.1.0-draft)

Profile for **one workbook: an ordered composition of worksheets** that cite `prim.measure` / `prim.metric` (and structure-only rows). Family name: `prim.workbook`.

Not OKF. Not a spreadsheet engine. The `.xlsx` / site grid is a view.

---

## 1. Split

| | prim.workbook | worksheet | prim.measure | prim.metric |
|---|---|---|---|---|
| Unit | the book | one sheet face | durable identity | series + proof |
| Authority | `workbook.json` | `worksheet.json` | `measure.json` | `metric.json` |
| Values | never | never (cites only) | definition only | receipt-backed series |

Compose, don’t merge. Size-1 workbooks are valid.

---

## 2. Face (`index.md`)

```yaml
---
profile: workbook
workbook_version: "0.1.0"
type: workbook
workbook_id: workbook:acme:acme-metrics
title: Acme Metrics
status: draft
workbook: workbook.json
compose:
  - worksheets/plan
  - worksheets/actuals
connectors:
  - warehouse
  - supabase
---
```

Required: `profile: workbook`, `workbook_version`, `type: workbook`, `workbook_id`, `title`, `status`, `workbook`.

`workbook_id` is immutable: `workbook:<namespace>:<slug>`.

`compose:` lists worksheet packs (relative directories with `index.md` + `worksheet.json`). Cite; do not copy.

`connectors:` names Prim Tools the book may use for prove/publish. Not pack types.

---

## 3. Store

```
<pack>/
  index.md              # face
  workbook.json         # REQUIRED — composition authority
  log.md                # strongly recommended
  worksheets/           # composed worksheet packs
  measures/             # optional co-located measure packs
  metrics/              # optional co-located metric packs
  views/                # generated grids / scorecards — never authority
```

Interchange: `.prim.zip` whose root is this directory (or a single top-level folder containing it).

---

## 4. Canonical model (`workbook.json`)

Required: `format`, `version`, `workbook_id`, `title`, `periods`, `worksheets`.

`format` MUST be `prim.workbook`.

### Worksheets

```json
"worksheets": [
  {
    "n": 1,
    "id": "plan",
    "role": "expected",
    "pack": "worksheets/plan",
    "title": "Plan · expected"
  },
  {
    "n": 2,
    "id": "actuals",
    "role": "actuals",
    "pack": "worksheets/actuals",
    "title": "SQL · actuals"
  }
]
```

| Field | Required | Notes |
|---|---|---|
| `n` | yes | Contiguous `1..N` |
| `id` | yes | Stable sheet id |
| `role` | yes | `expected` \| `actuals` \| `other` |
| `pack` | yes | Relative worksheet pack |
| `title` | yes | Human face label |

Hard rules:
- At least one `expected` and one `actuals` worksheet for proof-oriented books (recommended; required for proof UI).
- `expected` worksheets are frozen plan / answer-key faces. They may include structure-only rows.
- `actuals` worksheets are views. Cell values MUST resolve from cited `prim.metric` receipts or connector prove — never authored literals in the worksheet store.
- Proof is computed between matching row cites on `expected` vs `actuals`.

### Periods

```json
"periods": ["2025-10", "2025-11", "2026-03"]
```

Shared period vector for the book. Worksheets may mark periods `non_calc` / Forecast in their exceptions ledger.

---

## 5. Worksheet pack

```
worksheets/<id>/
  index.md
  worksheet.json
```

`worksheet.json` required fields: `format` (`prim.worksheet`), `version`, `worksheet_id`, `title`, `role`, `rows`.

### Rows

```json
"rows": [
  { "n": 8, "kind": "measure", "cites": "measure:acme:acme-revenue", "label": "Acme Revenue" },
  { "n": 20, "kind": "structure", "label": "Costs" },
  { "n": 40, "kind": "metric", "cites": "metric:acme:fuel-per-truck-hour", "label": "Fuel per Truck Hour" }
]
```

| `kind` | Meaning |
|---|---|
| `measure` | cites a `prim.measure` |
| `metric` | cites a `prim.metric` |
| `structure` | header / spacer / banner — not a measure |
| `non_calc` | labeled Forecast or otherwise not Actual |

Not every plan row is a measure or metric. Do not shoehorn.

---

## 6. Measure & metric (atoms)

Until standalone `prim.measure` / `prim.metric` profiles ship, packs MAY embed:

```
measures/<slug>/measure.json
metrics/<slug>/metric.json
```

**measure.json** — identity only: `measure_id`, `label`, `units`, `grain`, `denominator`, `exclusions`, `definition`.

**metric.json** — series + proof: `metric_id`, `cites_measures` (optional), `periods` → values via `receipt` / connector ref, never sheet literals as authority.

ODWF row contracts (`rows/r*.json` + `runs/*`) are a valid seed/receipt source.

---

## 7. Viewer

Surface tool: `workbook-editor` (cites `workbook`).

Must:
- Open both worksheets (tabs)
- Render structure vs measure vs metric distinctly
- Show proof gap for cited metrics (expected vs actuals)
- Expose connector status (warehouse / publish store) without owning credentials in the pack
- Never treat `views/` or site HTML as the store
- Accept a dropped `.prim.zip` / `.zip` in-browser without uploading the pack

This repository’s [`viewer/`](viewer/) is the public drag-drop surface. Category player `prim-viewer` hosts this type once registered.

---

## 8. Do not

- Mint `prim.surface` or `prim.connector` pack types
- Author actuals by typing into the actuals worksheet
- Force every sheet row into measure/metric
- Replace ODWF; workbook composes proof, ODWF remains a proof pack profile
- Drown in web code — the pack is the product; the site is a view
- Commit private customer packs to the public example tree
