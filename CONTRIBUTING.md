# Contributing your recordings

The **test set** (93 prompts x 1 approved take = 93 clips at 5s each) is
required. The **train set** (93 prompts x 2 approved takes = 186 clips,
roughly 30-45 minutes) is optional — `record.py` asks for your consent
before recording it. You can retry a take as
many times as you want before approving it — only approved takes count.

## 0. Prerequisites

- *Some* Python 3 (any recent version) and `git` — that's genuinely it.
  `setup.py` handles the rest, including finding a Python 3.10+
  interpreter on your system automatically if the one you have isn't
  new enough (`pywhispercpp`, used for live transcription, requires
  3.10+ and fails to even import on 3.9 and older).
- A working microphone, in as quiet a room as you can manage

No compiler, cmake, or manual whisper.cpp build needed — see step 2.

## 1. Clone

```
git clone https://github.com/ayla011/ai231-me2-voice-data.git
cd ai231-me2-voice-data
```

## 2. Set up (one-time)

```
python3 setup.py     # macOS/Linux
python setup.py      # Windows
```

This builds its own `.venv` in this folder (searching your system for a
3.10+ Python first if the one that ran this script is too old), installs
`requirements.txt` into it, and checks for an existing whisper model
and downloads the default (`base.en`, ~140MB) only if you don't already
have it, so your first recording session doesn't stall on a download. Windows, macOS, and Linux all just work — the whisper binary
comes prebuilt inside the `pywhispercpp` package. Safe to re-run; it
reuses `.venv` if it's already there and looks fine.

If it can't find any Python 3.10+ anywhere, it'll tell you and point you
to https://python.org/downloads/ (or `brew install python@3.12` on
macOS) — install one and re-run.

## 3. Record, transcribe, judge, approve

Run with `.venv`'s own python directly, so there's no dependence on your
shell's PATH:

```
.venv/bin/python scripts/record.py --speaker-id <yourid>            # macOS/Linux
.venv\Scripts\python.exe scripts\record.py --speaker-id <yourid>    # Windows
```

(Or `source .venv/bin/activate` / `.venv\Scripts\activate` once, then
just `python scripts/record.py ...` for the rest of the session.)

Use the `speaker_id` convention your group agreed on (see
`docs/drive_folder_structure.md`) — it becomes both your output folder
name and your Drive folder name, so get it right the first time.

First it asks whether you want to donate training data, telling you how
many prompts and recordings that involves. `y` = record train set, then
test set. `n` = test set only.

For each prompt, one take at a time:

1. It prints the prompt. Press Enter, speak within the recording window.
2. whisper.cpp transcribes what it heard and shows it next to the
   expected text (with a rough WER, just as a hint).
3. You decide: `Enter` = keep this take, `r` = retry, `p` = play it back
   first, `s` = skip this prompt, `q` = stop (safe to resume later).

Nothing gets written to `manifest.csv` or saved as a `.wav` until you
press `Enter` to keep it — so **by the time a take is saved, you've
already approved it**. There's no separate validation pass; what you
upload is what's used.

For the numeric/time prompts (`TIMER`, `ALARM`, `TEMPERATURE`,
`BRIGHTNESS`), don't be surprised if whisper's transcript looks
"different" even when your recording is fine — it often writes "20%"
for spoken "20 percent". Trust your ear (use `p` to play it back) over
the WER number; the transcript is there to catch actual
silence/mumbles/misreads, not to gate on exact string matches.

Options:
- `--train-takes 3` / `--test-takes 2` — approved recordings per prompt
  in each set (defaults 2 and 1)
- `--yes-train` / `--no-train` — answer the consent question up front
- `--labels TIMER ALARM` — only record specific intents (default: all)
- `--resume` — skip prompts that already have enough approved takes in
  your manifest (to redo a specific one anyway, delete its row from
  `manifest.csv` and its `.wav` first, then run with `--resume`)
- `--model small.en` — use a bigger/more accurate whisper model instead
  of the default `base.en` (downloaded only if not already installed)

## 4. Upload

You'll have `recordings/<yourid>/train/` (if you donated) and
`recordings/<yourid>/test/`. Upload them to **separate** Drive folders:
`train/` -> `raw/train/<yourid>/`, `test/` -> `raw/test/<yourid>/`,
following `docs/drive_folder_structure.md` exactly (folder name = your
`speaker_id`). Don't commit recordings to this git repo — see
`.gitignore`; audio lives on Drive only.
