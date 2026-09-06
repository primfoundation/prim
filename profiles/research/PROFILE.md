---
format: prim-profile
manifest_version: "0.1"
id: primfoundation/research
name: Research Prim
version: "0.3.0-dev.1"
maturity: development
description: Durable investigations with questions, evidence, claims, uncertainty, review, and continuation independent of a particular agent.
license: MIT
kinds:
  - investigation
legacy_aliases:
  - orf
resources:
  specification: SPEC.md
  examples: examples
extensions:
  primfoundation:
    status-note: Discovery prototype only; Research vNext instance validation and ORF migration are not implemented.
---
# Research Prim

Preserve the investigation, not merely the report. Another human or agent should
be able to establish what was asked, what was examined, why a conclusion was
reached, what contradicts it, and what remains to be done.

This is the first profile-publication prototype. The metadata describes the
package; it does not certify its publisher or its research. The human-facing
specification is in [SPEC.md](SPEC.md). Examples are explicitly illustrative.

## Independence

This directory can move to another repository without changing its declared
identity. The identity spelling is a provisional namespace convention, not a
claim of ownership of a universal name. No repository field is required.

The `orf` alias is historical metadata, not an instruction to reinterpret old
files. ORF 0.2.0 continues to use its original specification and validator.
There is no automatic alias resolution or migration in this slice.

## Trust boundary

Opening this profile does not run code, fetch evidence, approve research, or
transmit a user's investigation. A manifest pass means metadata and declared
local resource paths were checked. It does not mean a research instance passed,
the publisher was authenticated, or the package is secure.
