# Why prim.workbook exists

An Excel file is a frozen view with cells as authority. A metrics sheet, a warehouse receipt, and a website that tried to *be* the spreadsheet — that is the failure mode this profile exists to avoid.

**prim.workbook is Excel’s shape as a Prim.** Worksheets, rows, periods. Underneath: `prim.measure`, `prim.metric`, connectors to a warehouse and a publish store. Proof and provenance instead of cells as truth.

- **Compose, don’t merge.** A workbook cites worksheets. Worksheets cite measures and metrics (or mark structure-only rows). Same pattern as `prim.video` → `prim.scene`.
- **`workbook.json` is authority for composition.** Values live in cited packs / receipts — not pasted into the workbook face.
- **The expected face stays frozen.** One worksheet is the plan / answer-key face, including non-measure rows.
- **Actuals are a view.** Another worksheet resolves from live prove. Never hand-typed numbers as authority.
- **Proof is the gap.** Expected vs actuals, with provenance on the actuals side.
- **Connectors are Prim Tools**, not pack types. Warehouse proves; a publish store publishes.

Don’t send the spreadsheet — send the prim.
