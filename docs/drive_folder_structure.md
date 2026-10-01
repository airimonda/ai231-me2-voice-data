# Shared Drive folder structure

Create one shared Drive folder (e.g. `AI231-ME2-Voice-Data`) and share it
with the class as **Editor, restricted to class members** — do not set it
to "anyone with the link." This folder holds actual voice recordings of
your classmates, which is different from the GitHub repo (code + schema
only, no voices) that's fine to keep public.

## Upload steps (for each recorder)

1. After you finish `record.py` (and everything's approved), you'll have
   `recordings/<your-speaker-id>/train/` (only if you chose to donate
   training data) and `recordings/<your-speaker-id>/test/`, each with
   `.wav` files and one `manifest.csv`.
2. Go to the shared Drive folder: **`AI231-ME2-Voice-Data/raw/`**
3. **Train and test go in separate folders.** Upload `train/` into
   `raw/train/` and `test/` into `raw/test/`, each as a folder named
   after your speaker id:
   ```
   AI231-ME2-Voice-Data/raw/train/<your-speaker-id>/
   AI231-ME2-Voice-Data/raw/test/<your-speaker-id>/
   ```
4. **Your Drive folder name must exactly match the `--speaker-id` you
   used when recording** — lowercase, no spaces (e.g. `juandelacruz` or
   your student number `2024-12345`). Whatever convention the group
   agrees on, use it exactly — this is what lets everyone's data merge
   automatically later.
5. Don't rename files or hand-edit `manifest.csv` after the fact.
6. If you record more later (added takes, fixed something), upload into
   that *same* folder to add/overwrite files — don't create a second
   folder for yourself.
7. Nothing goes to GitHub — the repo is code/schema only. Drive is audio
   only.

## Layout

```
AI231-ME2-Voice-Data/              (shared Drive folder root)
  raw/
    train/
      <speaker_id>/                one folder per contributor who donated training data
        manifest.csv               written by record.py -- every row is
                                    already status=approved
        TIMER_V1_1_t1.wav
        ...
    test/
      <speaker_id>/                one folder per contributor
        manifest.csv
        TIMER_V1_1_t1.wav
        ...
  _merged/                         maintainer-only output of
                                    scripts/build_master_manifest.py
                                    (master_manifest.csv + pooled stats)
```
