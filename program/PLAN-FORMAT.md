# Program ledger contract

`plan.json` is the source of program status; `ROADMAP.md` is a deterministic view.
`format_version` is currently integer 1. The record includes mission, observation
date, actual execution/publication state, workstreams, milestones, requirements,
evidence references, whole-life domains, and cross-cutting coverage lenses.

Each workstream has a unique stable ID, name, and delivery responsibility:
Foundation, reference implementation, or ecosystem. Each milestone has a name
and an explicit acceptance gate. Each requirement has its own ID, workstream,
outcome title, acceptance criterion, milestone, owner role, status, dependencies,
required evidence stages, retained evidence IDs, and a note.

An owner role describes coordination responsibility, not authorization to make
legal, governance, spending, or sensitive-access decisions. A milestone number
is a sequencing guide, not a promised date or automatic completion state.

An evidence reference has an ID, a stage, a local retained file path, and a
summary. Stages are implementation, tests, review, release, deployment and
real_use. They are deliberately separate. Tests alone cannot satisfy a release,
deployment, or real-use gate.

The checker rejects missing or empty evidence files, unknown references, duplicate IDs and JSON keys, orphaned
workstreams/milestones, dependency cycles, missing acceptance/owners, unsupported
status, blocked requirements without reasons, invalid evidence paths, and
completed requirements without all declared evidence stages or with unfinished
dependencies. Required evidence cannot be an empty list.

The checker is not a truth oracle. A report's existence does not establish that
its assertions are accurate, independently reviewed, signed, or produced by a
trusted runner. Human/CI review evaluates the acceptance criteria and authentic
results. Nor does a single-snapshot checker stop someone deleting a requirement;
Git review and the decision register govern scope changes. Requirements can be
added and legitimate completion recorded without changing test fixtures.

The initial map had 17 workstreams and 70 requirements. The current preserved
map has 79 requirements, including delivery control. This is a baseline decomposition, not a proof that no future obligation
can be discovered. New findings get stable IDs and explicit acceptance criteria.
