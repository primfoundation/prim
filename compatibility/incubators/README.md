# Preserved incubator baselines

These are byte-preserved, commit-pinned public source selections. They retain
legacy inventions while new Foundation profiles and consumer migrations are
designed. They are **not registered Foundation profiles** and are not loaded by
the Library, Hub, SDK or native app. Each upstream license remains in scope.

| Baseline | Preserved | Deliberately outside this import |
| --- | --- | --- |
| OPF 1.0.0 | Product graph specification, validator, original six validator tests and synthetic fixture | Editor, self-packet, product records; v0 conversion |
| Album 0.1.0 draft | Album specification and original validator | Player, media, example score and player state |
| OCSF 0.1.0 draft | Corporate Structure intention and specification skeleton | No upstream validator, schema or example exists at this revision |
| Scene 0.1.0 draft | Cinematic beat specification and validator | Renderer, branded examples, media and capture tooling |
| Video 0.1.0 draft | Ordered Scene composition specification and validator | Assembly runtime, media and original instance packs |

`baseline.json` records repository, exact source commit, selected paths, byte
length, SHA-256 and Git blob SHA-1. Source bytes are unchanged. Excluded files
remain in the source repository's history; this is not a full-history mirror or
an archive authorization. Corporate Structure's aspirational legal, financial
and trust claims are historical proposals, not verified Foundation guarantees.

Run `python tools/incubator_conformance.py` from the Foundation repository.
It verifies all selected blobs, exercises the pinned OPF CLI and upstream tests,
and runs synthetic Album cases through the original CLI in temporary folders.
Scene/Video fixtures exercise timing, references, authority separation and the
legacy sibling dependency. Video silently skips Scene validation when that
sibling is absent; the regression suite retains this unsafe acceptance as a gap.
It also preserves and rereads the selected files through an in-memory ZIP and
checks byte identity. This proves selected-file transport, not semantic migration.

Legacy validators have known unsafe-input gaps. Album's original implementation
accepts nonfinite durations, boolean numbers, unsupported version strings and
file references outside a pack. Regression probes document those limitations
using only temporary synthetic data. OPF also needs bounded JSON and malformed
event hardening. Neither validator is a sandbox or an approved runtime for
arbitrary downloaded packs. This test tool accepts no user pack path and runs
only the reviewed pinned executables with a timeout.

Next gates: define explicit semantic mappings and loss reports; implement safe
readers without silently changing the pinned baseline; prove positive and negative
migrations with a second reader; audit excluded tools and consumers; obtain
independent domain, privacy and licensing review where required. No original
repository is renamed, archived or made public by this import.
