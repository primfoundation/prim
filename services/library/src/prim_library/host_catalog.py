"""Portable, data-only creation kits for independently implemented offline hosts."""


def export_host_catalog(library, source_commit: str = "unrecorded") -> dict:
    kits = []
    for entry in library.snapshot()["definitions"]:
        meta = entry["metadata"]
        if "creation" not in entry["resources"]:
            continue
        kits.append({**library.kit(meta["id"], meta["version"]), "name": meta["name"]})
    return {"format": "prim-host-catalog", "version": 1,
            "source_commit": source_commit, "snapshot_sha256": library.snapshot_id,
            "trust": "Checksum pins contents; it does not authenticate a publisher or grant execution authority.",
            "kits": sorted(kits, key=lambda k: (k["profile_id"], k["version"]))}
