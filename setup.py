#!/usr/bin/env python3
"""One-shot setup for the AI231 ME2 voice-data pool.

This is NOT a packaging setup.py (nothing here gets installed as a
package) -- it's a plain bootstrap script. It creates its own `.venv` in
this folder, so you don't need a conda env or an already-configured venv
-- just *some* working Python 3 to kick it off. If that Python is too
old for pywhispercpp (3.10+), it searches for a newer one on your system
and uses that to build the venv instead of failing.

Usage:
  python3 setup.py     (macOS/Linux)
  python setup.py      (Windows)

What it does:
  1. Finds a Python 3.10+ interpreter (the one running this script if
     it qualifies, otherwise searches common alternates).
  2. Creates .venv/ with that interpreter.
  3. Installs requirements.txt into .venv.
  4. Checks whether the default whisper model (base.en) is already on
     your machine; downloads it (~140MB) only if it isn't, so your first
     recording session doesn't stall on a download mid-prompt.

Afterward, run scripts with .venv's own python directly -- this avoids
any "python: command not found" / PATH weirdness entirely:
  .venv/bin/python scripts/record.py --speaker-id <yourid>          (macOS/Linux)
  .venv\\Scripts\\python.exe scripts\\record.py --speaker-id <yourid>  (Windows)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
VENV_DIR = REPO_ROOT / ".venv"
MIN_PYTHON = (3, 10)
DEFAULT_MODEL = "base.en"

# Checked in order; first one that's actually >= MIN_PYTHON and runs wins.
CANDIDATE_COMMANDS: list[list[str]] = [
    [sys.executable],
    ["python3.13"], ["python3.12"], ["python3.11"], ["python3.10"],
    ["py", "-3.13"], ["py", "-3.12"], ["py", "-3.11"], ["py", "-3.10"],  # Windows launcher
    ["python3"], ["python"],
]


def python_version_of(cmd: list[str]) -> tuple[int, int] | None:
    exe = shutil.which(cmd[0])
    if exe is None:
        return None
    try:
        result = subprocess.run(
            [*cmd, "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        major, minor = result.stdout.split()
        return (int(major), int(minor))
    except ValueError:
        return None


def find_suitable_python() -> list[str]:
    seen: set[tuple[str, ...]] = set()
    best_cmd: list[str] | None = None
    best_version: tuple[int, int] = (0, 0)
    for cmd in CANDIDATE_COMMANDS:
        key = tuple(cmd)
        if key in seen:
            continue
        seen.add(key)
        version = python_version_of(cmd)
        if version and version >= MIN_PYTHON and version > best_version:
            best_cmd, best_version = cmd, version
    if best_cmd is None:
        sys.exit(
            f"Could not find a Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ interpreter "
            f"anywhere on this system (checked: "
            f"{', '.join(' '.join(c) for c in CANDIDATE_COMMANDS)}).\n"
            f"pywhispercpp fails to even import on 3.9 and older, so this isn't "
            f"optional. Install a newer Python from https://python.org/downloads/ "
            f"(or via your OS package manager / Homebrew: brew install python@3.12), "
            f"then re-run this script."
        )
    print(f"Using {' '.join(best_cmd)} (Python {best_version[0]}.{best_version[1]}) to build .venv")
    return best_cmd


def venv_python_path() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def check_path_is_venv_safe() -> None:
    """Python's venv module refuses to build under a path containing
    os.pathsep (':' on macOS/Linux, ';' on Windows) -- that character
    would corrupt PATH inside every activate script. Catch this up front
    with a clear fix instead of letting venv creation crash mid-install."""
    if os.pathsep in str(REPO_ROOT):
        sys.exit(
            f"This repo's path contains '{os.pathsep}', which Python's venv "
            f"module refuses to build a venv under (it's the PATH separator "
            f"character -- having it in the venv's path would break every "
            f"activate script).\n"
            f"Path: {REPO_ROOT}\n"
            f"Fix: move or re-clone this repo somewhere without a "
            f"'{os.pathsep}' anywhere in the path, e.g.:\n"
            f"  git clone https://github.com/ayla011/ai231-me2-voice-data.git ~/ai231-me2-voice-data\n"
            f"then re-run setup.py from there."
        )


def main():
    check_path_is_venv_safe()

    if VENV_DIR.exists():
        vpy = venv_python_path()
        if vpy.exists() and (python_version_of([str(vpy)]) or (0, 0)) >= MIN_PYTHON:
            print(f".venv already exists and looks fine ({vpy}) -- reusing it.")
        else:
            print(".venv exists but is missing or too old -- rebuilding it.")
            shutil.rmtree(VENV_DIR)

    if not VENV_DIR.exists():
        base_python = find_suitable_python()
        print(f"Creating .venv ...")
        subprocess.run([*base_python, "-m", "venv", str(VENV_DIR)], check=True)

    vpy = str(venv_python_path())

    print("\nInstalling dependencies into .venv ...")
    subprocess.run([vpy, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([vpy, "-m", "pip", "install", "-r", str(REPO_ROOT / "requirements.txt")], check=True)

    print("\nChecking for an existing whisper model...")
    subprocess.run(
        [vpy, "-c",
         "import sys; sys.path.insert(0, 'scripts'); "
         f"from whisper_utils import resolve_model; resolve_model('{DEFAULT_MODEL}')"],
        check=True, cwd=REPO_ROOT,
    )

    print("\nSetup complete. Run scripts with .venv's own python directly:")
    if sys.platform == "win32":
        print(r"  .venv\Scripts\python.exe scripts\record.py --speaker-id <yourid>")
    else:
        print("  .venv/bin/python scripts/record.py --speaker-id <yourid>")
    print("(Or activate .venv first, then just `python scripts/record.py ...`.)")


if __name__ == "__main__":
    main()
