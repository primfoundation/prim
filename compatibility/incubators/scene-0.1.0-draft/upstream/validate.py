#!/usr/bin/env python3
"""Fail-closed checks for a prim.scene pack."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def validate(pack: Path) -> list[str]:
    err: list[str] = []
    face = pack / "index.md"
    scene_p = pack / "scene.json"
    if not face.is_file():
        err.append("missing index.md")
    if not scene_p.is_file():
        err.append("missing scene.json")
        return err
    try:
        s = json.loads(scene_p.read_text())
    except json.JSONDecodeError as e:
        return [f"scene.json: {e}"]

    for k in ("format", "version", "scene_id", "title", "duration", "fps", "size", "intent", "camera", "objects"):
        if k not in s:
            err.append(f"scene.json missing {k}")
    if s.get("format") != "prim.scene":
        err.append("format must be prim.scene")
    dur = s.get("duration")
    if not isinstance(dur, (int, float)) or dur <= 0:
        err.append("duration must be > 0")
        return err
    cam = s.get("camera") or {}
    keys = cam.get("keys") or []
    if not keys:
        err.append("camera.keys empty")
        return err
    times = [k.get("t") for k in keys]
    if times[0] != 0:
        err.append("first camera key t must be 0")
    if abs(float(times[-1]) - float(dur)) > 1e-6:
        err.append(f"last camera key t={times[-1]} must equal duration={dur}")
    for a, b in zip(times, times[1:]):
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float)) and b > a):
            err.append("camera key t must be strictly increasing")
            break
    for obj in s.get("objects") or []:
        if "id" not in obj or "kind" not in obj or "position" not in obj:
            err.append(f"object missing id/kind/position: {obj!r}")
            continue
        oid = obj["id"]
        okeys = obj.get("keys")
        if okeys is None:
            continue
        if not okeys:
            err.append(f"object {oid}: keys empty")
            continue
        times = [k.get("t") for k in okeys]
        if times[0] != 0:
            err.append(f"object {oid}: first key t must be 0 (got {times[0]})")
        try:
            last_t = float(times[-1])
        except (TypeError, ValueError):
            err.append(f"object {oid}: last key t={times[-1]} is not a number")
            last_t = None
        if last_t is not None and abs(last_t - float(dur)) > 1e-6:
            err.append(f"object {oid}: last key t={times[-1]} must equal duration={dur}")
        for a, b in zip(times, times[1:]):
            if not (isinstance(a, (int, float)) and isinstance(b, (int, float)) and b > a):
                err.append(f"object {oid}: key t must be strictly increasing (got {times})")
                break
        for k in okeys:
            pos = k.get("position")
            if not (isinstance(pos, list) and len(pos) == 3):
                err.append(f"object {oid}: key t={k.get('t')} position must be a 3-vector")
    gkeys = (s.get("group") or {}).get("keys")
    if gkeys:
        times = [k.get("t") for k in gkeys]
        if times[0] != 0:
            err.append("group: first key t must be 0")
        try:
            last_t = float(times[-1])
        except (TypeError, ValueError):
            err.append(f"group: last key t={times[-1]} is not a number")
            last_t = None
        if last_t is not None and abs(last_t - float(dur)) > 1e-6:
            err.append(f"group: last key t={times[-1]} must equal duration={dur}")
        for a, b in zip(times, times[1:]):
            if not (isinstance(a, (int, float)) and isinstance(b, (int, float)) and b > a):
                err.append("group key t must be strictly increasing")
                break
    for t in s.get("type") or []:
        inn, full = t.get("in"), t.get("full")
        if inn is None or full is None or not (0 <= inn < full <= dur):
            err.append(f"type times out of range: {t!r}")
    audio = s.get("audio") or {}
    if "file" in audio:
        ap = pack / audio["file"]
        if not ap.is_file():
            err.append(f"audio.file missing: {audio['file']}")
    rnd = pack / "renderer.html"
    if rnd.is_file():
        m = re.search(r"window\.__duration\s*=\s*([0-9.]+)", rnd.read_text())
        if m and abs(float(m.group(1)) - float(dur)) > 1e-6:
            err.append(
                f"warning-as-fail v0.1: renderer.html __duration={m.group(1)} "
                f"≠ scene.json duration={dur}"
            )
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
