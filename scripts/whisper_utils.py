"""Locate an already-downloaded whisper.cpp (ggml) model so nothing is
downloaded twice.

Used by setup.py and record.py. Needs pywhispercpp importable (run it with
.venv's python). Running this file directly prints the model path if found,
or exits 1:

  .venv/bin/python scripts/whisper_utils.py base.en
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def candidate_dirs() -> list[Path]:
    """Folders where a ggml model file may already live, most likely first."""
    from pywhispercpp.constants import MODELS_DIR

    dirs: list[Path] = []
    env = os.environ.get("WHISPER_MODEL_DIR")
    if env:
        dirs.append(Path(env).expanduser())
    dirs.append(Path(MODELS_DIR))
    home = Path.home()
    dirs += [
        home / ".cache" / "whisper",
        home / ".cache" / "whisper.cpp",
        home / "whisper.cpp" / "models",
        Path.cwd() / "models",
    ]
    return dirs


def find_model(name: str) -> str | None:
    """Return the path of an existing, non-empty model file, else None.
    `name` may be a pywhispercpp model name (e.g. 'base.en') or a path to a
    .bin file."""
    p = Path(name).expanduser()
    if p.suffix == ".bin":
        return str(p) if p.is_file() and p.stat().st_size > 0 else None
    fname = f"ggml-{name}.bin"
    for d in candidate_dirs():
        f = d / fname
        if f.is_file() and f.stat().st_size > 0:
            return str(f)
    return None


def resolve_model(name: str) -> str:
    """Existing model path if one is found; otherwise download it (the only
    case where a download happens) and return its path."""
    found = find_model(name)
    if found:
        print(f"Whisper model '{name}' already installed: {found} -- skipping download.")
        return found
    from pywhispercpp.utils import download_model

    print(f"Whisper model '{name}' not found on this machine -- downloading it now (one-time)...")
    path = download_model(name)
    if not path:
        sys.exit(f"Could not download whisper model '{name}'. Check the name and your internet connection.")
    return path


if __name__ == "__main__":
    hit = find_model(sys.argv[1] if len(sys.argv) > 1 else "base.en")
    if hit:
        print(hit)
    else:
        sys.exit(1)
