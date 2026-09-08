#!/usr/bin/env python3
"""Fail-closed checks for a prim.video pack. Compose, don't merge."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# prim.scene validator lives in the sibling repo when both are cloned
SCENE_VALIDATE = Path(__file__).resolve().parents[1] / "prim.scene" / "validate.py"


def validate(pack: Path) -> list[str]:
    err: list[str] = []
    if not (pack / "index.md").is_file():
        err.append("missing index.md")
    vp = pack / "video.json"
    if not vp.is_file():
        err.append("missing video.json")
        return err
    try:
        v = json.loads(vp.read_text())
    except json.JSONDecodeError as e:
        return [f"video.json: {e}"]

    for k in ("format", "version", "video_id", "title", "scenes"):
        if k not in v:
            err.append(f"video.json missing {k}")
    if v.get("format") != "prim.video":
        err.append("format must be prim.video")

    forbidden = {"camera", "objects", "type", "keys", "pos", "look"}
    hit = forbidden & set(v.keys())
    if hit:
        err.append(f"video.json must not hold scene authority keys: {sorted(hit)}")

    scenes = v.get("scenes") or []
    if not scenes:
        err.append("scenes empty")
        return err
    ns = [s.get("n") for s in scenes]
    if ns != list(range(1, len(scenes) + 1)):
        err.append(f"scenes n must be 1..N contiguous, got {ns}")

    durations = []
    for s in scenes:
        bad = forbidden & set(s.keys())
        if bad:
            err.append(f"scene entry n={s.get('n')} must not hold {sorted(bad)}")
        if "pack" not in s or "cites" not in s:
            err.append(f"scene n={s.get('n')} needs pack and cites")
            continue
        sp = (pack / s["pack"]).resolve()
        if pack not in sp.parents and sp != pack:
            err.append(f"pack escapes root: {s['pack']}")
            continue
        if not (sp / "index.md").is_file() or not (sp / "scene.json").is_file():
            err.append(f"not a prim.scene pack: {s['pack']}")
            continue
        sj = json.loads((sp / "scene.json").read_text())
        if sj.get("scene_id") != s["cites"]:
            err.append(f"cites {s['cites']!r} ≠ scene_id {sj.get('scene_id')!r}")
        durations.append(float(sj.get("duration") or 0))
        if SCENE_VALIDATE.is_file():
            import importlib.util
            spec = importlib.util.spec_from_file_location("scene_validate", SCENE_VALIDATE)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            serr = mod.validate(sp)
            err.extend(f"{s['pack']}: {e}" for e in serr)

    if "duration" in v and durations:
        if abs(float(v["duration"]) - sum(durations)) > 1e-3:
            err.append(f"video.duration {v['duration']} ≠ sum(scenes) {sum(durations)}")
    return err


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate.py <pack>", file=sys.stderr)
        return 2
    pack = Path(argv[1]).expanduser().resolve()
    errs = validate(pack)
    if errs:
        print("FAIL")
        for e in errs:
            print(" ", e)
        return 1
    print("ok", pack)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
