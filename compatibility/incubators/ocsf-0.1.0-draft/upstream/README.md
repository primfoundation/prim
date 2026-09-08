# OCSF — Open Corporate Structure Format

**A protocol / standard — not a corporate registry.**  
This repository is the **spec + validator + fictional examples**.  
Real group packs live private (next to the work or in org-private repos); this repository does not own live corporate data.

**OCSF v0.1.0-draft** is an additive profile of OKF v0.2.  
Every OCSF document is a valid OKF document.  
Renderers that know only OKF (e.g. [okflify](https://github.com/eidos-agi/okflify)) display it correctly and ignore profile keys.

```
OKF  — knowledge and trust                 https://github.com/eidos-agi/okflify
EMF  — human intent and durable memory     https://github.com/eidos-agi/emf
ORF  — research / investigation packs      https://github.com/eidos-agi/orf
OPF  — product graph                       https://github.com/eidos-agi/opf
ODFW — spreadsheet → bronze proof          https://github.com/eidos-agi/odwf
OPFF — personal finance packs              https://github.com/eidos-agi/opff
OMF  — meeting occurrences                 https://github.com/eidos-agi/omf
OCSF — corporate structure & capital       (this repo)
```

**Read [INTENTION.md](INTENTION.md) first.** It is load-bearing.

## What it models

- Legal entities (HoldCo, OpCo, SPV, AssetCo, …)
- Ownership and control graphs (with percentages, voting/economic rights)
- Capital instruments (share classes, equity, debt, intercompany loans, guarantees, options)
- Governance rights (board appointment, reserved matters)
- Cash-flow / upstreaming rules and constraints
- Evidence, provenance, and trust tiers for every material claim

## Install (when validator ships)

```bash
git clone https://github.com/eidos-agi/ocsf.git
cd ocsf
python3 -m pip install -e .
```

## Status

**v0.1.0-draft.** INTENTION and SPEC skeleton exist. Validator and minimal example coming next.

## License

MIT — Eidos AGI
