# ORF — OKF Research Format

**A protocol / standard — not a research warehouse.** This repo is the **spec + validator + examples**.
Research packs live next to the work (e.g. Squiddie `.research/<id>/`); this repo does not own the corpus.

**ORF v0.2.0** is an additive profile of [OKF v0.2](https://github.com/eidos-agi/okflify). Every ORF document is a valid OKF document. Renderers that know only OKF (e.g. [okflify](https://github.com/eidos-agi/okflify)) display it correctly and ignore profile keys.

```text
OKF  — knowledge and trust
EMF  — human intent and durable memory   https://github.com/eidos-agi/emf
ORF  — research / investigation packs    (this repo)
OPF  — product graph                     https://github.com/eidos-agi/opf
ODFW — spreadsheet → bronze proof        https://github.com/eidos-agi/odfw
OPFF — personal finance packs            https://github.com/eidos-agi/opff
```

**Read [SPEC.md](SPEC.md).**

## Install

```bash
git clone git@github.com:eidos-agi/orf.git
cd orf
pip install -e .
```

## Validate

```bash
python3 -m orf.validate --selftest
python3 -m orf.validate examples/orf-minimal
python3 -m orf.validate --strict examples/orf-minimal
orf-validate examples/orf-minimal

# negative example (expect FAIL)
python3 -m orf.validate examples/orf-bad-done-without-go; echo exit=$?
```

## What it checks

| Rule | Level |
|------|--------|
| `okf_version: "0.2"` | error |
| `orf_version` is `X.Y.Z` and `X.Y == okf_version` | error |
| Pack face has `orf_version` | error |
| `status: done` ⇒ `approval: go` | error |
| `approval: go` / planned+ ⇒ non-empty `question` | error |
| `CONFIRMED` needs ≥2 independent source hosts | error |
| Agent-authored `type: intent` | error |
| Capital `verdict` on ORF | warn |
| Missing `log.md` | warn |

## Consumers

| Consumer | Role |
|----------|------|
| [eidos-squiddie](https://github.com/eidos-agi/eidos-squiddie) | Research harness that **writes** ORF packs |
| [eidos-memory-labs](https://github.com/eidos-agi/eidos-memory-labs) | Studies OKF-family formats (links here) |
| [okflify](https://github.com/eidos-agi/okflify) | Renders ORF-labeled packs |
| [opff](https://github.com/eidos-agi/opff) | Sibling OKF profile (personal finance; not research) |

## History

ORF started inside the Squiddie repo (`eidos-squiddie/orf/`). Canonical home is now **this repository**. Squiddie depends on sibling/install of `orf`; it is no longer the protocol home.

## License

MIT — Eidos AGI
