# AI231 ME2 — Voice Data Pool

Recording tool for pooling classmates' voice samples for the AI231
Machine Exercise 2 (on-device Voice Command Model) group dataset. Every
contributor reads the same fixed prompt list and records two sets: an
optional **train** set (you're asked for consent first, and told how many
prompts it involves) and a **test** set (always recorded); for each take, whisper.cpp
transcribes it immediately and the contributor judges on the spot
whether to keep it or retry. Nothing gets saved until approved, so
everything that reaches the shared pool is already clean.

No compiler, cmake, or manual whisper.cpp build required — the whisper
model runs through [pywhispercpp](https://github.com/absadiki/pywhispercpp),
which ships prebuilt binaries for Windows, macOS, and Linux. The model is
only downloaded if it isn't already on your machine — setup and recording
both scan for an existing copy first.

**Scope & privacy:** this repo (code, prompt schema, docs) is public and
contains no one's voice. The actual recordings go to a separate,
access-restricted Drive folder — never here. See
`docs/drive_folder_structure.md`.

## Quickstart

You need *some* Python 3 installed to kick this off — that's it.
`setup.py` builds its own `.venv` in this folder and, if the Python that
ran it is older than 3.10 (which `pywhispercpp` requires), it
automatically searches your system for a newer one and uses that
instead. No conda env or pre-made venv needed.

```
git clone https://github.com/ayla011/ai231-me2-voice-data.git
cd ai231-me2-voice-data
python3 setup.py                              # macOS/Linux — use `python setup.py` on Windows
```

Then run everything with `.venv`'s own python, so there's never a
"python not found" surprise from your shell's PATH:

```
.venv/bin/python scripts/record.py --speaker-id <yourid>            # macOS/Linux
.venv\Scripts\python.exe scripts\record.py --speaker-id <yourid>    # Windows
```

(Or activate `.venv` first — `source .venv/bin/activate` /
`.venv\Scripts\activate` — then just `python scripts/record.py ...`.)

`record.py` first asks whether you want to donate training data (it tells
you how many prompts/recordings that is). Answer **yes** to record the
train set and then the test set; answer **no** to record the test set
only. Then upload the train and test sets to **separate** Drive folders
(see below). Full walkthrough: **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## Uploading your recordings

1. After `record.py` finishes (everything in it is already approved),
   you'll have, under `recordings/<your-speaker-id>/`:
   ```
   train/   .wav files + manifest.csv   (only if you said yes to donating)
   test/    .wav files + manifest.csv
   ```
2. Go to the shared Drive folder: **`AI231-ME2-Voice-Data/raw/`**
3. **Upload the train and test sets into separate folders — never mix
   them.** Upload `train/` into `raw/train/` and `test/` into `raw/test/`,
   each under a folder named after your speaker id, so it lands as:
   ```
   AI231-ME2-Voice-Data/raw/train/<your-speaker-id>/
     manifest.csv
     *.wav
   AI231-ME2-Voice-Data/raw/test/<your-speaker-id>/
     manifest.csv
     *.wav
   ```
   (If you declined to donate training data, upload only the `test/` set.)
4. **Your Drive folder name must exactly match the `--speaker-id` you
   used when recording** — lowercase, no spaces (e.g. `juandelacruz` or
   your student number `2024-12345`), matching whatever convention the
   group agreed on. This is what lets everyone's data merge
   automatically later.
5. Don't rename files or hand-edit `manifest.csv` afterward.
6. Recording more later? Upload into that *same* folder to add/overwrite
   files — don't create a second folder for yourself.
7. Nothing goes to GitHub — this repo is code/schema only. Drive is
   audio only.

The Drive folder itself should be shared as **Editor, restricted to
class members** — not "anyone with the link" — since it holds actual
voice recordings. Full layout and maintainer-side details:
**[docs/drive_folder_structure.md](docs/drive_folder_structure.md)**.

## Layout

```
setup.py                     one-shot installer: builds .venv (finding a
                              3.10+ Python automatically if needed),
                              installs requirements, downloads the model only if absent
schema/prompts.csv          93 prompts: 13 fixed intents (3 phrasings each)
                             + 6 slotted intents (3 phrasings x 3 example
                             values each). One row = one utterance to say.
scripts/
  record.py                  consent question, then record -> whisper transcribes ->
                              you approve -> saved, one prompt at a time, into
                              recordings/<speaker_id>/train/ and /test/
  whisper_utils.py           finds an already-installed whisper model so it
                              is never downloaded twice
  build_master_manifest.py   maintainer-only: merges every contributor's
                              manifest.csv (from Drive raw/train + raw/test) into one master CSV
docs/drive_folder_structure.md   how the shared Drive folder is organized
CONTRIBUTING.md                   step-by-step contributor guide
```

## How the live QA works

`record.py` records one take, transcribes it with whisper.cpp right
away, and shows you both the expected prompt and what whisper heard
(plus a rough WER as a hint). You decide whether to keep it, retry, or
play it back first — nothing is written to disk or to `manifest.csv`
until you approve it. That's the whole validation step: by construction,
every row in an uploaded `manifest.csv` has `status=approved`. There's
no separate batch QA pass to run before uploading. whisper.cpp here is
strictly a live QA aid for this pooling step, not the model being built.

## Prompt schema source

`schema/prompts.csv` is generated from the group's shared prompt sheet
(the 3-variation / 3-example-value table). If the schema changes, edit
that CSV directly — it's the single source of truth all scripts read
from.
