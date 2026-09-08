# Open Product Format

[![CI](https://github.com/eidos-agi/opf/actions/workflows/validate.yml/badge.svg)](https://github.com/eidos-agi/opf/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

OPF v1 is a canonical durable product graph. `product.json` owns entities,
typed relationships, structural hierarchy, lifecycle, and temporal events;
Markdown and folders are optional content projections.

OPF carries product intent, outcomes, journeys, surfaces, states, interactions,
decisions, work, authority, evidence, proof, gaps, and time as first-class graph
records. It is intentionally incompatible with the earlier frontmatter profile.

## Install

```bash
git clone https://github.com/eidos-agi/opf.git
cd opf
python -m pip install -e ".[dev]"
```

## Use

```bash
opf-validate --selftest
opf-validate examples/v1-product
python3 -m unittest discover -s tests -q
```

Validation enforces typed relationship direction, one ordered structural parent,
root reachability, provenance, content containment, and canonical temporal events.

## Agent integration

Agents can invoke `opf-validate <pack>` as a deterministic publication gate.
Exit status `0` means the canonical graph passed; nonzero output names each
path, rule, severity, and actionable failure detail.

For guided product-definition work, use the bundled [`use-opf` skill](skills/use-opf/SKILL.md).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) to develop OPF. Report vulnerabilities
using [SECURITY.md](SECURITY.md). Participation follows our
[Code of Conduct](CODE_OF_CONDUCT.md).

OPF is released under the [MIT License](LICENSE).

See [SPEC.md](SPEC.md) and [the v1 reference graph](examples/v1-product/product.json).
