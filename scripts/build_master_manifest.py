#!/usr/bin/env python3
"""Maintainer-only: merge every classmate's manifest.csv (downloaded from
the shared Drive `raw/` folder) into one master CSV for the actual ME2
dataset build. Not needed by contributors.

Usage:
  python scripts/build_master_manifest.py --raw-dir ~/Drive/AI231-ME2-Voice-Data/raw   # contains train/ and test/ \
      --out data/master_manifest.csv
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", required=True, help="local sync of the shared Drive raw/ folder")
    ap.add_argument("--out", default="data/master_manifest.csv")
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    manifests = sorted(raw_dir.glob("*/*/manifest.csv"))  # raw/<train|test>/<speaker_id>/manifest.csv
    if not manifests:
        raise SystemExit(f"No train|test/<speaker_id>/manifest.csv found under {raw_dir}")

    all_rows = []
    status_counts = Counter()
    speaker_counts = Counter()
    fieldnames: list[str] | None = None
    for manifest_path in manifests:
        speaker_dir = manifest_path.parent.name
        split_dir = manifest_path.parent.parent.name
        with manifest_path.open() as f:
            reader = csv.DictReader(f)
            if fieldnames is None:
                fieldnames = reader.fieldnames + ["source_path"]
            for row in reader:
                if row.get("speaker_id") != speaker_dir:
                    print(f"WARNING: {manifest_path}: speaker_id={row.get('speaker_id')!r} "
                          f"!= folder name {speaker_dir!r}")
                if row.get("split") != split_dir:
                    print(f"WARNING: {manifest_path}: split={row.get('split')!r} "
                          f"!= folder name {split_dir!r}")
                row["source_path"] = str((manifest_path.parent / row["filename"]).relative_to(raw_dir))
                status_counts[row.get("status", "unvalidated")] += 1
                speaker_counts[(split_dir, speaker_dir)] += 1
                all_rows.append(row)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)

    print(f"Merged {len(manifests)} manifests, {len(all_rows)} rows -> {out_path}\n")
    print("By status:")
    for status, n in status_counts.most_common():
        print(f"  {status:>14}: {n}")
    print("\nBy speaker:")
    for (split, speaker), n in sorted(speaker_counts.items()):
        print(f"  {split:>5} {speaker:>20}: {n}")

    not_approved = sum(n for s, n in status_counts.items() if s != "approved")
    if not_approved:
        print(f"\n{not_approved} rows have status != approved -- record.py only ever writes "
              "'approved', so this manifest was likely hand-edited. Check it before using.")

    worst = sorted(all_rows, key=lambda r: float(r.get("wer") or 0), reverse=True)[:10]
    if worst:
        print("\nHighest-WER approved rows (contributors already judged these fine -- "
              "optional spot-check only, not a requirement to fix):")
        for row in worst:
            print(f"  wer={float(row['wer']):.2f}  {row['source_path']}  "
                  f"expected=\"{row['text']}\"  whisper=\"{row['whisper_transcript']}\"")


if __name__ == "__main__":
    main()
