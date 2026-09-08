# prim.scene — SPEC (v0.1.0-draft)

Profile for **one cinematic scene**. Family name: `prim.scene`.

Not OKF. Not a video. Not CAD (`3d-forge`). The mp4 is a projection.

---

## 1. Split

| | prim.scene | prim.video | video-3d-forge | 3d-forge |
|---|---|---|---|---|
| Store | one beat | ordered scenes | renderer / capture | SLDPRT → GLB |
| Authority | `scene.json` | `video.json` | none (tool) | mesh |
| Open | `ui` | `ui` | `video-3d-forge capture` | `sld2glb` |

Do not mint `prim.surface`. The player is a tool.

---

## 2. Face (`index.md`)

```yaml
---
profile: scene
scene_version: "0.1.0"
type: scene
scene_id: scene:eidos-agi:ident-v1
title: Eidos ident v1
status: draft
scene: scene.json
renderer: renderer.html
---
```

Required: `profile: scene`, `scene_version`, `type: scene`, `scene_id`, `title`, `status`, `scene`.

`scene_id` is immutable: `scene:<namespace>:<slug>`.

Optional face path: `renderer` (HTML that implements `window.__seek(t)` and `window.__duration`).

---

## 3. Store

```
<pack>/
  index.md           # face
  scene.json         # REQUIRED — sole scene authority
  log.md             # strongly recommended
  renderer.html      # projection; may lag scene.json in v0.1
  assets/            # fonts, marks, textures cited by scene.json
  audio/             # cited beds (not the song library)
  renders/           # generated frames / mp4 — never authority
```

Interchange: `.prim.zip` whose root is this directory.

---

## 4. Canonical model (`scene.json`)

Required: `format`, `version`, `scene_id`, `title`, `duration`, `fps`, `size`, `intent`, `camera`, `objects`.

`format` MUST be `prim.scene`. `duration` is seconds, `> 0`. `fps` is a positive integer. `size` is `[width, height]` pixels.

### Camera

```json
"camera": {
  "keys": [
    { "t": 0.0, "pos": [16.5, 7.4, 22.0], "look": [1.4, 0.4, 0.2], "fov": 46 }
  ]
}
```

- `t` is seconds from scene start. Keys MUST be strictly increasing in `t`.
- First key `t` MUST be `0`. Last key `t` MUST equal `duration`.
- `pos` and `look` are world-space `[x,y,z]`. `fov` is vertical degrees.

A key that would place the camera **inside** a solid object is a defect. v0.1 records this as LAW; mechanical intersection lands when the renderer can measure it.

### Objects

Each object: `id`, `kind`, `position`. Optional `material`, `rotation`, `scale`.

v0.1 kinds: `sphere`, `plane`, `group`. Unknown kinds are allowed; the renderer may ignore them.

`position` is the static pose for the whole duration when the object has no `keys`. It remains required even when `keys` are present (the t=0 rest, and the pose a renderer uses if it cannot sample).

#### Object keys (optional)

An object MAY carry `keys`, the same kind of timed samples as camera keys:

```json
"keys": [
  { "t": 0.0, "position": [0.0, 0.08, 0.0], "scale": 0.08 },
  { "t": 16.0, "position": [-2.207, 0.42, 0.0], "scale": 1.0 }
]
```

- `t` is seconds from scene start. Keys MUST be strictly increasing in `t`.
- First key `t` MUST be `0`. Last key `t` MUST equal `duration`.
- `position` is world-space `[x,y,z]`. `scale` is optional (uniform).
- When `keys` is omitted, `objects[].position` (and optional static `scale`) is the pose for the whole duration.
- A camera key inside a solid is still a camera defect. Object keys do not relax that rule.

The renderer samples these keys at `window.__seek(t)`. It MUST NOT invent object motion that is not in `scene.json`.

### Group (optional)

```json
"group": {
  "rotation_z_deg": 0,
  "keys": [
    { "t": 0.0, "rotation_y_deg": 0, "rotation_z_deg": 0 },
    { "t": 16.0, "rotation_y_deg": 4320, "rotation_z_deg": 0 }
  ]
}
```

`keys` follow the same `t` rules as camera keys. `rotation_y_deg` / `rotation_z_deg` are degrees. A PID (or any other) spin must be **baked into these keys**. The renderer samples; it does not run the controller.

### Type (optional)

On-screen type is not the story of the scene. Motion is. If present:

```json
"type": [
  { "id": "word", "in": 12.2, "full": 13.1, "text": "Eidos AGI" }
]
```

`in` / `full` are seconds. `in` < `full` ≤ `duration`.

### Audio (optional)

```json
"audio": { "file": "audio/bed.m4a", "cites": "track 1 last 16s" }
```

`file` is a pack-relative path. The scene does not own the song. Ident-length fades belong here as a *cite of a bed*, not a music-forge split.

---

## 5. Compose

A scene MAY `compose:` brand (`obif`) or other scenes it samples. It MUST NOT copy those packs' authority files into `scene.json`.

A scene is not a video. If you need more than one beat, that is `prim.video`.

---

## 6. Validator

`python3 validate.py <pack>`

Hard fail: missing `scene.json`, missing required keys, non-increasing camera times, last camera key ≠ duration, object keys present but empty / first t ≠ 0 / last t ≠ duration / non-increasing t / missing 3-vector position, type times out of range.

Warning: `renderer.html` present but `window.__duration` disagrees with `scene.json` (v0.1 dual-authority debt).
