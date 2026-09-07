# Migration from `primfoundation/prim.workbook`

Source selected for standards import:

- repository: `primfoundation/prim.workbook`
- sanitized source commit: `8e997f0e349d788c56722ea8bd0c3d0afbdb99e5`
- source `SPEC.md` blob: `2f5a66da6865b497379432c7f58c228d940787c9`
- source `INTENTION.md` blob: `50c6b3a416464226dccab523d477f36321280b23`

The selected branch removed Greenmark/Cerebro citations and uses fictional Acme material. The repository's earlier main/history contained a Cerebro/Greenmark sample, so that history is **not copied into this public profile package** and must be treated as a separate privacy/history review before repository archival or visibility changes.

## Preserved

- workbook is one ordered composition of worksheet packs;
- workbook/worksheet stores contain structure and citations rather than treating rendered cell values as authority;
- measure and metric atoms remain distinct concepts;
- expected versus actuals/proof semantics remain part of the profile;
- connector names are Prim Tools, not pack types or credentials;
- historical `prim.workbook` / `prim.worksheet` / measure / metric encodings are not silently renamed.

The sanitized source SPEC/INTENTION are retained under `legacy/` for direct review, with the original source blob IDs above as the byte-authority references.

## Changed only in publication architecture

The publishable unit is now `primfoundation/workbook`; its declared kinds include `workbook`, `worksheet`, `measure`, and `metric`. A repository is no longer the identity of each kind.

A development schema/template were added so the generic Foundation Library can create a blank root workbook locally. Those files are new reference tooling, not evidence that every legacy semantic rule is mechanically checked.

## Generated integration checkpoint

One-shot generation at branch commit `72223c7bac8d78d8dcbcf5458df54f55104296a4` committed the deterministic profile catalog, content-addressed Library resources, compiled Library snapshot, and the four-profile regression update, then removed the temporary generator. The generator's own complete Library unit run passed before that commit. Normal Foundation CI on this subsequent human-authored checkpoint is the durable acceptance gate; bot-authored workflow commits are not treated as a substitute when GitHub marks their follow-up runs `action_required`.

## Retirement gate for the old repository

Do not archive `prim.workbook` until sanitized fixtures and old consumers open through the new package; registry/Hub resolution points to the new profile without changing old pack interpretation; any viewer worth preserving has a successor; earlier repository history receives privacy review; real-use and rollback evidence are retained; and the old README points to this successor and last supported state.
