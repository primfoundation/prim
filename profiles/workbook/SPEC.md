# Workbook Prim — development contract

Profile package: `primfoundation/workbook@0.1.0-dev.1`.

Historical instance encoding retained for this migration: `prim.workbook` / `version: "0.1.0"`. The sanitized source specification is preserved under `legacy/SPEC-0.1.0-draft.md`; its source blob/commit are recorded in MIGRATION.md and remain the compatibility reference for historical packs while this package is reviewed.

## Durable model

A workbook is an ordered composition of worksheets. `workbook.json` is composition authority. Worksheets cite measures/metrics or declare structural rows. Values do not become authoritative merely because they appear in an XLSX, HTML grid, or worksheet face.

Kinds in this one profile package:

- `workbook` — ordered book composition;
- `worksheet` — one sheet face and its row citations;
- `measure` — durable identity/definition;
- `metric` — a series whose values cite receipts or connector proof.

These are kinds within one publishable profile package, not a requirement for four repositories.

## Authority and views

`workbook.json` is the authoritative workbook composition record. Rendered spreadsheets, websites and files under `views/` are projections.

A proof-oriented workbook can compose expected and actuals worksheets. Expected is a frozen plan/answer-key face; actuals resolve from cited metric receipts or connector proof rather than hand-authored literals.

Connectors are Prim Tools. Their names in a workbook never place credentials in the pack and never confer authority to access an external system.

## Generic creation-kit scope

The development schema checks the root `workbook.json` shape, supported roles, bounded IDs/paths, required fields and duplicate worksheet IDs through the generic Library rules.

The current generic kit does **not** establish all historical semantic rules: contiguous worksheet `n`, existence of cited subpacks, expected/actual proof coverage, receipt validity, source freshness, connector access, factual correctness, or publisher/reviewer identity remain separate checks.

Unknown JSON properties are retained so a new tool does not destroy extensions.

## Compatibility

Do not reinterpret old packs because this profile moved repositories. Historical `format`, `version`, IDs and relative worksheet paths remain meaningful as authored. Any future encoding change needs read-old/write-new policy, fixtures, loss reporting and rollback.

See [MIGRATION.md](MIGRATION.md).
