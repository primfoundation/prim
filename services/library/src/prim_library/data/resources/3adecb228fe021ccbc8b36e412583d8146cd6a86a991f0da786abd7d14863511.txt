# prim.person

Incubating. Authority is `person.json`. The face points at it.

View key: `person/person`. Unknown hosts fall back to the face.

## Face

```yaml
profile: person
type: person
title: Ada Lovelace
person: person.json
status: draft
```

`person` MUST resolve to a file in the pack named in this SPEC.

## Authority — `person.json`

| Field | Rule |
|-------|------|
| `id` | Required. Token `^[a-z][a-z0-9.-]*$`. |
| `name` | Required. Non-empty string. |
| `relate` | Optional string. How they relate (plain language). Alias: `relationship`. |
| `display_name` | Optional string. Short label for UI if different from `name`. |
| `phones` | Optional array of strings. |
| `emails` | Optional array of strings. |
| `note` | Optional string. Last useful note. |

No other file is authority. `log.md` is the category log.

Prims Contacts reads and writes this file under ~/Documents/Prims by default. It does not invent a parallel contacts store. A person pack is not an app user.

## Hard rejects

- Missing `index.md` or authority
- Face `profile` not `person`
- Missing `id` token or empty `name`

Default on-disk home: `~/Documents/Prims/person/<id>/`.

## Links (incubating — not stamped)

Need: a people graph. Person packs must link to other people and to other prims (calendar events, orgs, etc.).

**Not stamped.** Rolodex may write optional `links` on `person.json` for proven edges only. Validator does not yet require or enum-check them.

Provisional shape:

| Field | Rule |
|-------|------|
| `links` | Optional array of objects. |
| `links[].to` | Required. Path relative to profile root (`person/<id>`, `calendar-events/<slug>`, …). |
| `links[].kind` | Required. v0 enum: `family` \| `works-with` \| `attendee` \| `introduced` \| `same-org`. |
| `links[].as` | Optional. Role label (`father`, `coworker`). |
| `links[].evidence` | Required. Why this edge exists (`stated-family`, `calendar-event-receive`, …). |

Until stamped: do not invent kinds; do not write weak edges; keep `relate` / `relationship` as the human one-liner.

Gap: publish `person` on registry.prims.sh; stamp `links` here + in `validate.py`; add contacts-receive as the writer.
