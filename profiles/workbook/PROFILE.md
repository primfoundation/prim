---
format: prim-profile
manifest_version: "0.1"
id: primfoundation/workbook
name: Workbook Prim
version: "0.1.0-dev.1"
maturity: development
description: Ordered workbook composition whose worksheets cite measures and metrics; spreadsheet files are views, not authority.
license: MIT
kinds:
  - workbook
  - worksheet
  - measure
  - metric
resources:
  specification: SPEC.md
  migration: MIGRATION.md
  legacy-specification: legacy/SPEC-0.1.0-draft.md
  legacy-intention: legacy/INTENTION.md
  creation: creation.json
  schema: schema/record.schema.json
  template: template.json
  examples: examples
extensions:
  primfoundation:
    source-repository: primfoundation/prim.workbook
    source-commit: 8e997f0e349d788c56722ea8bd0c3d0afbdb99e5
    source-status: sanitized-public-head
---
# Workbook Prim

A workbook is an ordered composition of worksheet faces. Worksheets cite durable measures and metrics; the workbook does not turn rendered cells into the source of truth.

This package migrates the sanitized `prim.workbook` invention into the repository-independent profile system. Repository location is not part of the profile identity. Read [MIGRATION.md](MIGRATION.md) before changing compatibility with historical `prim.workbook` packs.

The package is still development maturity. Its generic creation kit validates a bounded structural subset; it does not yet implement every semantic rule in the legacy specification or prove live metric receipts.
