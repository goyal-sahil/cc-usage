# Installing cc-usage on a new PC

A step-by-step guide for installing and running `cc-usage` on a fresh machine.

## Prerequisites

You need:
- **Python 3.11 or newer** — check with `python --version`
- **Git** — check with `git --version`
- **Claude Code** already installed and used at least once (so there's data in `~/.claude/projects/`)

If Python is missing on Windows, install it from [python.org/downloads](https://www.python.org/downloads/) and tick **"Add Python to PATH"** during install.

---

## Step 1 — Clone the repo

```bash
git clone https://github.com/goyal-sahil/cc-usage.git
cd cc-usage
```

---

## Step 2 — Install the tool

Pick **one** of these. `pipx` is recommended because it isolates the install and puts `cc-usage` on your PATH globally.

**Option A — pipx (recommended)**

```bash
# one-time setup, if you don't have pipx yet
python -m pip install --user pipx
python -m pipx ensurepath
# restart the terminal, then:
pipx install .
```

**Option B — pip**

```bash
pip install .
```

---

## Step 3 — Verify the install

```bash
cc-usage --help
```

You should see the flag list (`--project`, `--sessions-dir`, `--output`, `--json`, `--prices`, `--update-prices`, `--quiet`).

If `cc-usage` is "not found" on Windows after `pipx`, close and reopen the terminal — `ensurepath` only takes effect in new shells.

---

## Step 4 — Run it on a Claude Code project

`cd` into any folder where you've used Claude Code, then:

```bash
cc-usage
```

It auto-detects the matching `~/.claude/projects/<encoded-path>/` folder and writes results to `.usage/` in the current directory.

---

## Step 5 — Look at the output

```
.usage/
├── report.md        ← human-readable summary
├── detail.csv       ← one row per API call
├── by_session.csv
├── by_day.csv
└── by_model.csv
```

For a demo, open `report.md` — it's the most visual.

---

## Step 6 — (Optional) Analyse a different project

```bash
cc-usage --project "C:\path\to\some\other\project"
```

Or with JSON export:

```bash
cc-usage --json
```

---

## Step 7 — (Optional) Refresh pricing

If Anthropic updates their rates:

```bash
cc-usage --update-prices
```

Edits go into `~/.config/cc-usage/prices.json` and are auto-loaded next run.

---

## Step 8 — (Optional) Ignore output in your project

Add this line to your project's `.gitignore`:

```
.usage/
```
