# prim.video — SPEC (v0.1.0-draft)

Profile for **one video: an ordered collection of `prim.scene` packs**. Family name: `prim.video`.

Not OKF. Not a scene. The mp4 is a projection.

---

## 1. Split

| | prim.video | prim.scene |
|---|---|---|
| Unit | the piece | one beat |
| Authority | `video.json` (order) | `scene.json` (camera, objects, duration) |
| Duration | sum of cited scenes | `scene.json.duration` |

A video with one scene is still a video. Size-1 collections are valid.

---

## 2. Face (`index.md`)

```yaml
---
profile: video
video_version: "0.1.0"
type: video
video_id: video:eidos-agi:ident-v1
title: Eidos AGI ident
status: draft
video: video.json
compose:
  - scenes/ident
---
```

Required: `profile: video`, `video_version`, `type: video`, `video_id`, `title`, `status`, `video`.

`video_id` is immutable: `video:<namespace>:<slug>`.

`compose:` lists scene packs (relative directories containing `index.md`). Required when scenes live beside this pack. Cite; do not copy.

---

## 3. Store

```
<pack>/
  index.md           # face
  video.json         # REQUIRED — order authority
  log.md             # strongly recommended
  scenes/            # composed prim.scene packs (optional layout; paths are in video.json)
  renders/           # generated assembly — never authority
```

Interchange: `.prim.zip` whose root is this directory.

---

## 4. Canonical model (`video.json`)

Required: `format`, `version`, `video_id`, `title`, `scenes`.

`format` MUST be `prim.video`.

### Scenes

```json
"scenes": [
  { "n": 1, "pack": "scenes/ident", "cites": "scene:eidos-agi:ident-v1" }
]
```

| Field | Required | Notes |
|---|---|---|
| `n` | yes | Contiguous `1..N` |
| `pack` | yes | Relative directory that is a `prim.scene` pack (`index.md` + `scene.json`) |
| `cites` | yes | That pack's `scene_id` |

Hard rules:

1. `n` is `1..N` with no gaps.
2. `pack` resolves under this pack root and validates as `prim.scene`.
3. `cites` MUST equal `scene.json.scene_id` in that pack.
4. **`video.json` MUST NOT contain camera keys, objects, or type overlays.** Those live in the scene. If you need a different fly, edit the scene (or cite a new one).
5. Video duration is computed: sum of cited `scene.json.duration`. Do not store a competing duration unless it equals that sum (optional `duration` field; mismatch is a fail).

---

## 5. Validator

`python3 validate.py <pack>`

Hard fail: missing scenes, broken n, missing scene pack, `cites` mismatch, camera/objects/type keys present on `video.json` or scene entries, optional `duration` ≠ sum.
