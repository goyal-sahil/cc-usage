# cc-usage

Analyse Claude Code token usage from local JSONL session files.

Reads `~/.claude/projects/<project>/` — no API calls, no credentials needed.

## Install

```bash
pip install .
# or for isolated global install:
pipx install .
```

## Usage

Run from inside any Claude Code project:

```bash
cc-usage
```

This auto-detects the sessions directory for the current working directory and writes results to `.usage/`.

### Options

```
cc-usage [--project DIR] [--sessions-dir DIR] [--output DIR] [--json] [--quiet]
```

| Flag | Description |
|------|-------------|
| `--project DIR` | Analyse a different project (path to that project's root) |
| `--sessions-dir DIR` | Explicit path to the `.claude/projects/<id>/` folder |
| `--output DIR` | Output directory (default: `.usage/` in cwd) |
| `--json` | Also write `report.json` |
| `--quiet` | Suppress progress output |

### Examples

```bash
# Current project, default output
cc-usage

# Another project
cc-usage --project ~/my-other-project

# Explicit sessions dir + JSON output
cc-usage --sessions-dir ~/.claude/projects/C--Users-me-myproject --json

# Pipe totals into another tool
cc-usage --quiet && cat .usage/report.md
```

## Output Files

| File | Contents |
|------|----------|
| `report.md` | Human-readable Markdown summary |
| `detail.csv` | One row per API call |
| `by_session.csv` | Aggregated per session |
| `by_day.csv` | Aggregated per calendar day |
| `by_model.csv` | Aggregated per model |
| `report.json` | All tables as JSON (requires `--json`) |

## How It Works

Claude Code writes a JSONL file per session to `~/.claude/projects/<encoded-cwd>/`.  
Each assistant turn contains a `usage` object with input, output, and cache token counts.  
`cc-usage` reads these files locally and estimates cost using Anthropic's published pricing.

### Pricing Used

| Model | Input | Cache Write | Cache Read | Output |
|-------|------:|------------:|-----------:|-------:|
| claude-opus-4 | $15 | $18.75 | $1.50 | $75 |
| claude-sonnet-4 | $3 | $3.75 | $0.30 | $15 |
| claude-haiku-4 | $0.80 | $1.00 | $0.08 | $4 |

Prices are per million tokens. Unknown models fall back to Sonnet 4 rates.

## Adding to a Project

Add to any project's `.gitignore`:

```
.usage/
```

Then run `cc-usage` whenever you want a fresh report.
