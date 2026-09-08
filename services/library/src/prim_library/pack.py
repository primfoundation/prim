"""Read a pinned local record without executing a profile or following references."""
from pathlib import Path
from .library import LibraryError, load_json, MAX_DOCUMENT


def read_pack(library, source: Path) -> dict:
    source = source.absolute()
    if not source.is_dir() or any(p.is_symlink() for p in [source, *source.parents]):
        raise LibraryError("select a local directory without symlinks")

    def read(name):
        path = source / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_DOCUMENT:
            raise LibraryError("invalid or oversized local Prim file")
        return load_json(path.read_bytes())

    pin = read("prim-definition.lock.json")
    if not isinstance(pin, dict) or any(not isinstance(pin.get(k), str) for k in ["profile_id", "version", "definition_sha256"]):
        raise LibraryError("invalid definition lock")
    library.get(pin["profile_id"], pin["version"], pin["definition_sha256"])
    kit = library.kit(pin["profile_id"], pin["version"])
    record = read(kit["authority_file"])
    result = library.validate(pin["profile_id"], pin["version"], record)
    return {"pin": pin, "record": record, "validation": result}
