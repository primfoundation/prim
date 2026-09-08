#!/usr/bin/env python3
"""Fail-closed checks for a prim.album pack."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def validate(pack: Path) -> list[str]:
    err: list[str] = []
    face = pack / "index.md"
    album_p = pack / "album.json"
    if not face.is_file():
        err.append("missing index.md")
    else:
        text = face.read_text()
        if not re.search(r"^profile:\s*album\s*$", text, re.M):
            err.append("index.md profile must be album")
        if not re.search(r"^type:\s*album\s*$", text, re.M):
            err.append("index.md type must be album")
    if not album_p.is_file():
        err.append("missing album.json")
        return err
    try:
        a = json.loads(album_p.read_text())
    except json.JSONDecodeError as e:
        return [f"album.json: {e}"]

    for k in ("format", "version", "album_id", "title", "tracks"):
        if k not in a:
            err.append(f"album.json missing {k}")
    if a.get("format") != "prim.album":
        err.append("format must be prim.album")
    for k in ("volume", "playing", "index", "transport"):
        if k in a:
            err.append(f"album.json must not contain player state: {k}")

    tracks = a.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        err.append("tracks must be a non-empty list")
        return err

    ids: set[str] = set()
    total = 0.0
    for i, t in enumerate(tracks, start=1):
        if not isinstance(t, dict):
            err.append(f"track {i} is not an object")
            continue
        if t.get("n") != i:
            err.append(f"track n must be contiguous 1..N (got n={t.get('n')} at {i})")
        tid = t.get("id")
        if not isinstance(tid, str) or not tid:
            err.append(f"track {i} missing id")
        elif tid in ids:
            err.append(f"duplicate track id: {tid}")
        else:
            ids.add(tid)
        if not t.get("title"):
            err.append(f"track {i} missing title")
        dur = t.get("duration")
        if not isinstance(dur, (int, float)) or dur <= 0:
            err.append(f"track {i} duration must be > 0")
            dur = 0.0
        total += float(dur)
        src = t.get("source")
        if not isinstance(src, dict) or "kind" not in src:
            err.append(f"track {i} missing source.kind")
            continue
        kind = src["kind"]
        if kind == "file":
            path = src.get("path")
            if not path:
                err.append(f"track {i} file source missing path")
            elif not (pack / path).is_file():
                err.append(f"track {i} file missing: {path}")
        elif kind == "patch":
            bars = src.get("bars")
            if not isinstance(bars, int) or bars <= 0:
                err.append(f"track {i} patch.bars must be a positive integer")
            bpm = t.get("bpm")
            if isinstance(bars, int) and bars > 0 and isinstance(bpm, (int, float)) and bpm > 0 and dur:
                expect = bars * 4 * 60 / float(bpm)
                if abs(float(dur) - expect) > 1e-3:
                    err.append(
                        f"track {i} duration={dur} must equal bars*4*60/bpm={expect:.6f}"
                    )
        elif kind == "cite":
            if not src.get("album_id") or not src.get("track"):
                err.append(f"track {i} cite source needs album_id and track")
        else:
            err.append(f"track {i} unknown source.kind: {kind}")
        for bad in ("camera", "objects", "volume", "playing"):
            if bad in t:
                err.append(f"track {i} must not contain {bad}")

    top = a.get("duration")
    if top is not None:
        if not isinstance(top, (int, float)) or abs(float(top) - total) > 1e-3:
            err.append(f"album duration={top} must equal sum of tracks={total:.6f}")
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
