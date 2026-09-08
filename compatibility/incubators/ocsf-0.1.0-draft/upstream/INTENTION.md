# OCSF Intention

**Status:** load-bearing product intention for the public format  
**Instance dogfood:** private group packs must share this intention

---

## One sentence

OCSF is the open format for **self-contained, evidence-backed packages that make a corporate group’s legal entities, ownership graph, capital instruments, governance rights, and cash-flow rules machine-verifiable** — so agents (and humans) can reason about claim priority, risk boundaries, related-party exposure, and upstreaming without tribal knowledge.

---

## Why this exists

Capital structure and parent/subsidiary design are currently scattered across:

- Cap tables (spreadsheets or proprietary systems)
- Incorporation documents and bylaws
- Intercompany loan notes and IP licenses
- Board resolutions and investor rights agreements
- Tax filings and LEI records

Agents cannot reliably answer:

- Who ultimately owns / controls this OpCo?
- What is the seniority of this intercompany claim vs external debt?
- Can cash legally move upstream today, or do covenants / solvency rules block it?
- Which documents prove the current ownership percentages?

OCSF turns those questions into first-class, dated, evidence-backed objects with fail-closed validators.

---

## Design commitments

1. **Additive OKF v0.2 profile** — every document remains a valid OKF document. Trust tiers, provenance, and `log.md` come for free. okflify can render the ownership graph.
2. **Graph-first** — entities, instruments, and typed relationships are first-class. A canonical `structure.json` (or equivalent) is the semantic authority; Markdown is optional projection.
3. **Evidence is mandatory** for material claims (ownership %, guarantees, intercompany terms, board rights). Provenance + content hash + trust tier required.
4. **Temporal** — every relationship and instrument carries effective dates and can be superseded. History lives in events + `log.md`.
5. **Validators are fail-closed** — ownership percentages must sum correctly, cycles must be justified, evidence must be present for high-stakes claims, distribution gates must pass before upstreaming is asserted.
6. **Interoperable** — prefer LEI as stable identity; provide clean export paths to BODS (beneficial ownership) and import paths from OCF (detailed equity).
7. **Public repo owns only the protocol** — real packs with live data stay private.

---

## What OCSF is not

- Not a company registry
- Not a tax or accounting system of record
- Not a replacement for executed legal documents (it references them)
- Not a beneficial-ownership disclosure format alone (it is broader; BODS remains the right tool for pure BO publishing)

---

## Success criteria

An agent that has never seen the group before can:

1. Load an OCSF pack
2. Validate it
3. Answer “who owns / controls X and on what evidence?”
4. Reconstruct the capital waterfall and distribution constraints
5. Produce an ownership graph (via okflify) that a human counsel would trust as a starting map

If those five hold, the format has succeeded.
