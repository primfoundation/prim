# Decision Prim — development contract

`decision.json` is authoritative; index and exports are views. `profile` and
`profile_version` pin this explicitly experimental definition, not a repository.
The schema requires a proposed/accepted/superseded/withdrawn state; accepted
records name an existing option, question, rationale and an actor as recorded.
An actor string does NOT authenticate anyone or authorize execution.

Use stable option IDs. Unknown JSON fields are retained. Corrections and
supersession must preserve prior documents; no distributed merge or identity
verification is implemented by this creation kit. Blank creation does not infer
a human's intent. Compare alternatives and record uncertainty in extensions.
