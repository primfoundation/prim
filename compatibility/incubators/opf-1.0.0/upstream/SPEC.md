# OPF v1.0 — Open Product Format

OPF is the canonical durable product graph used to shape, build, operate, and
audit a real product. Files and folders are storage projections. Their names,
locations, and ordering carry no product meaning.

## 1. Pack

```text
docs/opf/
  product.json          # required canonical model
  content/*.md          # optional human-readable entity bodies
  evidence/*            # optional native proof artifacts
  docs.json             # optional renderer presentation settings
```

`product.json` is the only semantic authority. Markdown links, frontmatter,
folder trees, renderer layouts, search indexes, and calendars do not add or
change entities or relationships.

```json
{
  "format": "opf",
  "version": "1.0",
  "product": "opf:voice-lab:product",
  "entities": [],
  "relationships": [],
  "events": []
}
```

## 2. Entities

Every entity has a stable `id`, `type`, `title`, lifecycle `status`, and
`provenance` naming who asserted it and how. `description`, `content`, and
type-specific properties are optional.

```json
{
  "id": "opf:voice-lab:surface:product-brief",
  "type": "surface",
  "title": "Product brief",
  "status": "proposed",
  "description": "Shows canonical product intent, product-promise policy, and evidence; live runtime commitments are external.",
  "content": "content/product-brief.md",
  "provenance": {
    "by": "agent:codex",
    "method": "translation of coordinator-supplied product direction"
  }
}
```

Allowed types are:

| family | entity types |
|---|---|
| root and structure | `product`, `area` |
| intent | `intent`, `user`, `problem`, `promise`, `outcome` |
| experience | `journey`, `moment`, `surface`, `state`, `interaction` |
| governance | `decision`, `authority` |
| delivery | `work` |
| assurance | `evidence`, `proof` |
| incompleteness | `gap` |

`promise` means a product-level value, policy, or capability assertion. It is
not a live work commitment: runtime Promise records, lifecycle, estimates,
approvals, and operational events belong to the system operating them, not an
OPF packet.

Allowed statuses are `proposed`, `active`, `blocked`, `validated`, `building`,
`operating`, `complete`, `retired`, and `rejected`. Status is current state;
the event log preserves how and when it changed.

### Decision context direction

A meaningful `decision` must preserve enough context to challenge it later,
not only its conclusion. The intended canonical shape is a `rationale` object:

```json
{
  "rationale": {
    "why": "Why this choice addresses the product problem now.",
    "problems": ["opf:voice-lab:problem:opaque-delayed-work"],
    "alternatives": [
      {
        "option": "Keep operational state in the voice session",
        "disposition": "ruled-out",
        "reason": "Session loss would erase supervisory continuity."
      }
    ],
    "alternatives_note": "Use when no alternatives were considered or the record is unknown.",
    "revisit_when": ["A durable replacement proves equivalent recovery across fresh sessions."]
  }
}
```

`why` and revisit conditions must be explicit. `problems` should resolve to
canonical problem entities when they exist. Alternatives are recorded only when
known; an empty list plus an honest `alternatives_note` is preferable to an
invented option. Decision authority remains `provenance`, `governed-by`, and the
actor on its `accepted` event. Evidence remains explicit `supported-by` links.

This is accepted model and validator direction, not an OPF 1.0 validator rule.
The current validator accepts the structured context but does not require or
semantically validate it; a deliberate migration and versioned validator change
must precede fail-closed enforcement.

## 3. Relationships

Relationships are first-class records with stable IDs. Meaning lives in their
typed direction, never in generic links.

```json
{
  "id": "opf:voice-lab:rel:journey-step-command",
  "type": "has-step",
  "from": "opf:voice-lab:journey:supervise-work",
  "to": "opf:voice-lab:moment:issue-command",
  "order": 0
}
```

| relationship | allowed source → target | meaning |
|---|---|---|
| `contains` | product→area; area→non-root; journey→moment; surface→state; state→interaction | canonical structural parent |
| `expresses` | product→intent | product anchors human intent |
| `for-user` | problem/promise/outcome/journey→user | user served |
| `addresses` | promise→problem | product promise answers problem |
| `serves` | promise/journey/moment/surface/interaction/work→outcome | advances outcome |
| `has-step` | journey→moment | ordered experience step |
| `uses` | moment→surface | surface encountered at a moment |
| `has-state` | surface→state | state visible on a surface |
| `allows` | state→interaction | interaction available in a state |
| `transitions-to` | interaction→state | resulting state |
| `realizes` | interaction→outcome | outcome reached by interaction |
| `decides` | decision→non-root | governed product assertion |
| `governed-by` | non-root→authority | authority owning the assertion |
| `implements` | work→promise/decision/surface/interaction/outcome | delivery target |
| `supported-by` | non-evidence→evidence | observation supporting assertion |
| `verified-by` | non-proof→proof | falsifiable gate covering assertion |
| `blocks` | gap→non-root | known unresolved blocker |
| `depends-on` | non-root→non-root | explicit dependency |
| `supersedes` | same-type non-root→same-type non-root | replacement lineage |

`has-step` requires integer `order`. `supersedes` requires matching entity types.

## 4. Deterministic hierarchy

Exactly one entity is `type: product` and is named by top-level `product`.
Every other entity has exactly one incoming `contains` relationship. The
containment graph is acyclic and every entity is reachable from the product.
Each `contains` has a unique nonnegative sibling `order`.

This tree is the canonical product hierarchy. Semantic relationships remain a
separate directed graph. A renderer may lay either view out differently, but it
must not infer hierarchy from folders, IDs, link degree, filenames, or dates.

## 5. Canonical events and time

All durable chronology is explicit in `events`:

```json
{
  "id": "opf:voice-lab:event:decision-accepted",
  "type": "accepted",
  "at": "2026-08-08T04:00:00Z",
  "subjects": ["opf:voice-lab:decision:voice-first"],
  "actor": "human:daniel",
  "detail": "Voice-first control accepted as product direction."
}
```

Event types are `created`, `updated`, `accepted`, `status-changed`, `observed`,
and `log`. Timestamps are RFC 3339 with a timezone. Every entity has exactly
one `created` event. Non-log events require resolvable subjects. `accepted`
events require an actor and decision subjects. A historic `log` event may have
an empty subject list; renderers must label that missing reference honestly and
must never guess one from prose.

Timeline and rendered log default to reverse chronological order. Equal
timestamps use later append position as the deterministic tie-breaker. Calendar
day/week/month/year views project this same event stream; calendar navigation
does not change chronology semantics.

## 6. Required projections

An OPF renderer should expose the same canonical model through:

- source/folder storage;
- canonical product hierarchy;
- typed concept/relationship graph;
- journey and experience flow;
- decisions and authority;
- timeline and day/week/month/year calendar;
- evidence and proof;
- unresolved gaps.

Search and recommendations index entity titles, descriptions, content, types,
statuses, and typed neighborhoods. Those indexes and all presentation settings
belong to the renderer and are never written back as product semantics.

## 7. Validation

Validation fails closed on malformed JSON, unsupported entity or relationship
types, unresolved endpoints, invalid typed directions, missing provenance,
unsafe content paths, invalid hierarchy, invalid timestamps, duplicate IDs,
missing creation events, and malformed decision acceptance.

Validation does not yet enforce decision `rationale`, alternative completeness,
or pre-implementation reconciliation. Those remain explicit roadmap gaps rather
than inferred guarantees.

```bash
python3 -m opf.validate docs/opf
```

OPF v1 is intentionally breaking. There is no v0 parser, migration layer,
fallback frontmatter model, or compatibility mode.
