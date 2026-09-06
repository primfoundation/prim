# Native Research draft — 0.3.0-dev.3

This is a new experimental record contract, not a relabeling of ORF.
`research.json` is authority. A lock records definition ID, version and complete
definition digest. The profile version is independent of the source grammar.

A draft can have an unknown question; an active or completed investigation must
name one. Completion records findings or an explicitly inconclusive outcome.
Claims retain a basis (attributed statement, observation, inference, estimate)
and assessed support state. Sources are distinct records; evidence links name
a claim, a source and a relation: cites/supports/contradicts/qualifies.
Citations are not silently upgraded to support. Supported claims must name at
least one declared supporting edge; validators do NOT verify its factual merits.

Activities and reviews retain attribution as RECORDED. Review acceptance is not
cryptographic identity, source independence, human approval or permission to act.
Structural checks cover IDs, references, required fields and basic states only.
Unknown JSON properties are retained; no validator fetches source URLs or imports
package code. The draft does not implement full revision/merge/freshness semantics.

For legacy ORF use the frozen compatibility tool. An automatic semantic migration
remains open because the old parser and labels need explicit interpretation.
This draft is evaluated alongside Person and Decision; the other four non-research
reference cases and two independent implementations are still acceptance gates.
