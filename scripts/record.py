#!/usr/bin/env python3
"""Guided recording session for the AI231 ME2 voice-data pool.

Walks through schema/prompts.csv one utterance at a time. For each take:
record -> whisper.cpp (via pywhispercpp) transcribes it immediately ->
you judge whether to keep it or retry, right there. Nothing is saved
until you approve it, so whatever ends up in your manifest.csv is
already the clean, final take -- there's no separate validation pass
before upload.

Two sets are recorded, into separate folders:
  recordings/<speaker-id>/train/   optional -- you're asked for consent first
  recordings/<speaker-id>/test/    always recorded

No manual whisper.cpp build needed -- pywhispercpp ships prebuilt
binaries for Windows/macOS/Linux. The whisper model is only downloaded if
it isn't already on your machine.

Run this with .venv's own python (built by `setup.py`), not your
system's -- e.g. `.venv/bin/python scripts/record.py ...` on macOS/Linux
or `.venv\\Scripts\\python.exe scripts\\record.py ...` on Windows.

Usage:
  .venv/bin/python scripts/record.py --speaker-id juandelacruz
  .venv/bin/python scripts/record.py --speaker-id juandelacruz --model small.en
  .venv/bin/python scripts/record.py --speaker-id juandelacruz --train-takes 3 --test-takes 2
  .venv/bin/python scripts/record.py --speaker-id juandelacruz --no-train   # skip the consent question, test set only
  .venv/bin/python scripts/record.py --speaker-id juandelacruz --yes-train  # skip the consent question, record both
  .venv/bin/python scripts/record.py --speaker-id juandelacruz --labels TIMER ALARM
  .venv/bin/python scripts/record.py --speaker-id juandelacruz --resume   # skip prompts already fully approved in each set
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit(
        f"Python 3.10+ required (found {sys.version_info.major}.{sys.version_info.minor}).\n"
        f"pywhispercpp itself breaks on import under 3.9 and older (it uses newer "
        f"type-hint syntax internally). Did you run this with .venv's python? "
        f"If you haven't run setup.py yet (or it's stale), run: python3 setup.py "
        f"(macOS/Linux) or python setup.py (Windows) -- then use .venv/bin/python "
        f"(or .venv\\Scripts\\python.exe on Windows) to run this script."
    )

import sounddevice as sd
import soundfile as sf
from pywhispercpp.model import Model

sys.path.insert(0, str(Path(__file__).resolve().parent))
from whisper_utils import resolve_model  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 16000
SPLITS = ("train", "test")
MANIFEST_FIELDS = [
    "speaker_id", "split", "prompt_id", "label", "type", "text", "slot_value",
    "take", "filename", "recorded_at", "whisper_transcript", "wer", "status",
]


def load_prompts(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def load_existing_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def normalize(text: str) -> list[str]:
    text = text.lower()
    text = text.replace("%", " percent")
    text = re.sub(r"(\d):(\d\d)", r"\1 \2", text)
    text = re.sub(r"[^a-z0-9' ]", " ", text)
    return text.split()


def word_error_rate(ref: list[str], hyp: list[str]) -> float:
    n, m = len(ref), len(hyp)
    if n == 0:
        return 0.0 if m == 0 else 1.0
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[n][m] / n


def record_clip(duration: float):
    print(f"  Recording for {duration:.1f}s... speak now.")
    audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()


def transcribe(model: Model, audio) -> str:
    segments = model.transcribe(audio, print_progress=False)
    text = " ".join(seg.text for seg in segments).strip()
    if text in ("[BLANK_AUDIO]", "[SILENCE]", "[NO SPEECH]"):
        return ""  # whisper.cpp's own silence tags -- treat as nothing heard
    return text


def record_and_approve(prompt: dict, take: int, split: str, args, model: Model) -> dict | None:
    """Record/transcribe/judge loop for one take. Returns the manifest
    row once approved, {"__quit__": True} on quit, or None if skipped."""
    expected_words = normalize(prompt["text"])

    while True:
        cmd = input("  [Enter to record, s=skip prompt, q=quit] > ").strip().lower()
        if cmd == "q":
            return {"__quit__": True}
        if cmd == "s":
            return None

        audio = record_clip(args.duration)
        print("  Transcribing...")
        hyp_text = transcribe(model, audio)
        wer = word_error_rate(expected_words, normalize(hyp_text)) if hyp_text else 1.0
        print(f"    expected: \"{prompt['text']}\"")
        print(f"    whisper:  \"{hyp_text or '(nothing heard)'}\"  (wer={wer:.2f})")

        decision = input("  [Enter=keep, r=retry, p=play back, s=skip prompt, q=quit] > ").strip().lower()
        if decision == "p":
            sd.play(audio, SAMPLE_RATE)
            sd.wait()
            decision = input("  [Enter=keep, r=retry, s=skip prompt, q=quit] > ").strip().lower()
        if decision == "q":
            return {"__quit__": True}
        if decision == "s":
            return None
        if decision == "r":
            continue

        filename = f"{prompt['prompt_id']}_t{take}.wav"
        out_dir = REPO_ROOT / "recordings" / args.speaker_id / split
        sf.write(str(out_dir / filename), audio, SAMPLE_RATE, subtype="PCM_16")
        return {
            "speaker_id": args.speaker_id,
            "split": split,
            "prompt_id": prompt["prompt_id"],
            "label": prompt["label"],
            "type": prompt["type"],
            "text": prompt["text"],
            "slot_value": prompt["slot_value"],
            "take": take,
            "filename": filename,
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "whisper_transcript": hyp_text,
            "wer": f"{wer:.3f}",
            "status": "approved",
        }


def ask_yes_no(question: str) -> bool:
    while True:
        ans = input(f"{question} [y/n] > ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("  Please answer y or n.")


def run_split(split: str, prompts: list[dict], takes_wanted: int, args, model: Model) -> bool:
    """Record one set (train or test). Returns True if the user quit early."""
    out_dir = REPO_ROOT / "recordings" / args.speaker_id / split
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.csv"
    existing = load_existing_manifest(manifest_path)
    approved_counts: dict[str, int] = {}
    for row in existing:
        approved_counts[row["prompt_id"]] = approved_counts.get(row["prompt_id"], 0) + 1

    print(f"\n=== {split.upper()} set: {len(prompts)} prompts, {takes_wanted} approved take(s) each ===\n")

    new_rows: list[dict] = []
    quit_early = False
    for i, prompt in enumerate(prompts, start=1):
        already = approved_counts.get(prompt["prompt_id"], 0)
        if args.resume and already >= takes_wanted:
            continue
        for take in range(already + 1, takes_wanted + 1):
            print(f"[{split} {i}/{len(prompts)}] ({prompt['label']}, take {take}/{takes_wanted}) say:")
            print(f"    \"{prompt['text']}\"")
            row = record_and_approve(prompt, take, split, args, model)
            if row is None:
                break  # skipped -- move to next prompt
            if row.get("__quit__"):
                quit_early = True
                break
            new_rows.append(row)
            print("  approved.\n")
        if quit_early:
            break

    if not new_rows:
        print(f"\nNo new {split} recordings.")
    else:
        with manifest_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
            w.writeheader()
            w.writerows(existing + new_rows)
        print(f"\nSaved {len(new_rows)} new approved {split} recordings. Manifest: {manifest_path}")
    return quit_early


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--speaker-id", required=True, help="your name or student number, no spaces (e.g. juandelacruz)")
    ap.add_argument("--prompts", default=str(REPO_ROOT / "schema/prompts.csv"))
    ap.add_argument("--model", default="base.en", help="pywhispercpp model name (downloaded only if not already installed) or path to a local .bin")
    ap.add_argument("--train-takes", type=int, default=2, help="approved recordings per prompt in the train set")
    ap.add_argument("--test-takes", type=int, default=1, help="approved recordings per prompt in the test set")
    ap.add_argument("--duration", type=float, default=5.0, help="seconds per take")
    ap.add_argument("--labels", nargs="*", default=None, help="only record these labels (default: all)")
    ap.add_argument("--resume", action="store_true", help="skip prompts already fully approved in your manifests")
    consent = ap.add_mutually_exclusive_group()
    consent.add_argument("--yes-train", action="store_true", help="donate training data without asking")
    consent.add_argument("--no-train", action="store_true", help="skip the train set without asking")
    args = ap.parse_args()

    prompts = load_prompts(Path(args.prompts))
    if args.labels:
        wanted = set(args.labels)
        prompts = [p for p in prompts if p["label"] in wanted]
    if not prompts:
        sys.exit("No prompts matched --labels; check schema/prompts.csv for valid label names.")

    print(f"Speaker: {args.speaker_id}\n")

    n_train = len(prompts) * args.train_takes
    if args.yes_train:
        donate = True
    elif args.no_train:
        donate = False
    else:
        mins = n_train * (args.duration + 3) / 60  # rough: recording + review time per clip
        print("Would you like to donate TRAINING data as well as the test set?")
        print(f"  Train set: {len(prompts)} prompts x {args.train_takes} take(s) = {n_train} recordings (roughly {mins:.0f} min).")
        print(f"  Test set:  {len(prompts)} prompts x {args.test_takes} take(s) = {len(prompts) * args.test_takes} recordings (always recorded).")
        donate = ask_yes_no("Donate training data?")

    sets = []
    if donate:
        sets.append(("train", args.train_takes))
    sets.append(("test", args.test_takes))
    print("Recording: " + " + ".join(name for name, _ in sets) + " set(s).")

    print(f"Loading whisper model '{args.model}'...")
    model = Model(resolve_model(args.model), redirect_whispercpp_logs_to=False)

    quit_early = False
    for split, takes in sets:
        if run_split(split, prompts, takes, args, model):
            quit_early = True
            break

    if quit_early:
        print(f"\nResume later with: {sys.executable} scripts/record.py "
              f"--speaker-id {args.speaker_id} {'--yes-train' if donate else '--no-train'} --resume --model {args.model}")
    print("\nUpload recordings/<speaker-id>/train/ and recordings/<speaker-id>/test/ to SEPARATE Drive folders -- see README.md.")


if __name__ == "__main__":
    main()
