#!/usr/bin/env python3
"""Compatibility entrypoint for the installed, read-only profile discovery tool."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/library/src"))
from prim_library.profiles import (MANIFEST, MAX_BYTES, ProfileError, discover_profiles,
                                   encode, inspect_profile, main, _local_path)

if __name__ == "__main__":
    raise SystemExit(main())
