# prim.album — SPEC (v0.1.0-draft)

Profile for **one record**. Family name: `prim.album`.

Not OKF. Not a song file. Not slides (`prim.deck`). Not a playable cart (`prim.arcade`). The player is a projection.

---

## 1. Split

| | prim.album | prim.deck | prim.arcade | prim.scene |
|---|---|---|---|---|
| Store | one record | slide records | a playable cart | one cinematic beat |
| Authority | `album.json` | deck file | the ROM / cart | `scene.json` |
| Open | `ui` / album-player | `deck-editor` | `prim-arcade` | `ui` |

Do not mint `prim.track`. Do not mint `prim.surface`. The player is a tool.

---

## 2. Face (`index.md`)

```yaml
---
profile: album
album_version: "0.1.0"
type: album
album_id: album:eidos-agi:siliconfall-score
title: Siliconfall Score
status: draft
album: album.json
---
```

Required: `profile: album`, `album_version`, `type: album`, `album_id`, `title`, `status`, `album`.

`album_id` is immutable: `album:<namespace>:<slug>`.

Optional face path: `player` (HTML/app that cites this pack).

---

## 3. Store

```
<pack>/
  index.md           # face
  album.json         # REQUIRED — sole album authority
  log.md             # strongly recommended
  audio/             # cited files (optional; never authority)
  art/               # cover stills (optional; never authority)
```

Interchange: `.prim.zip` whose root is this directory.

---

## 4. Canonical model (`album.json`)

Required: `format`, `version`, `album_id`, `title`, `tracks`.

`format` MUST be `prim.album`.

Optional: `artist`, `year`, `intent`, `liner`.

### Tracks

```json
"tracks": [
  {
    "n": 1,
    "id": "lobby",
    "title": "Lobby",
    "site": "Badge printers",
    "bpm": 118,
    "duration": 65.0847,
    "source": {
      "kind": "patch",
      "bars": 32,
      "root": 55.0,
      "cutoff": 420,
      "swing": 0.12,
      "drive": 0.35
    }
  }
]
```

| Field | Required | Notes |
|---|---|---|
| `n` | yes | Contiguous `1..N` |
| `id` | yes | Unique in the album. Stable. |
| `title` | yes | Track title |
| `duration` | yes | Seconds, `> 0` |
| `source` | yes | How the track sounds |
| `site` | no | Place / scene the track belongs to |
| `bpm` | no | Beats per minute |

Hard rules:

1. `n` is `1..N` with no gaps.
2. `id` values are unique.
3. **`album.json` MUST NOT contain player UI, transport state, or volume.** Those live in the tool.
4. A track is a record. It is not a nested pack.

### Source

`source.kind` is one of:

| kind | Required extra | Notes |
|---|---|---|
| `patch` | `bars` (positive integer) | Generative. Optional `root`, `cutoff`, `swing`, `drive`. If `bars` and `bpm` are both present, `duration` MUST equal `bars * 4 * 60 / bpm` within `1e-3`. |
| `file` | `path` | Pack-relative audio file. Must exist. |
| `cite` | `album_id`, `track` | Another album's track. Do not copy its source here. |

A licensed mix is not a valid `file` source for a public pack. Cite, or write an original patch.

Album duration is computed: sum of `tracks[].duration`. Optional top-level `duration` must equal that sum (mismatch is a fail).

---

## 5. Compose

An album MAY `compose:` a game, a brand (`brand`), or scenes it underscores. It MUST NOT copy those packs' authority files into `album.json`.

An album is not a cart. If you need a playable ROM, that is `prim.arcade`.

---

## 6. Validator

`python3 validate.py <pack>`

Hard fail: missing `album.json`, missing required keys, broken `n`, duplicate `id`, `duration` ≤ 0, unknown `source.kind`, missing file for `kind: file`, patch duration mismatch, optional album `duration` ≠ sum.
