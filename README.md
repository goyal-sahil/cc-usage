# cc-usage

Analyse Claude Code token usage from local JSONL session files.

Reads `~/.claude/projects/<project>/` — no API calls, no credentials needed.

## Install

```bash
pip install .
# or for an isolated global install:
pipx install .
```

## Usage

Run from inside any Claude Code project:

```bash
cc-usage
```

Auto-detects the sessions directory for the current working directory and writes results to `.usage/`.

### Options

| Flag | Description |
|------|-------------|
| `--project DIR` | Analyse a specific project by path (auto-detects its sessions dir) |
| `--sessions-dir DIR` | Explicit path to the `~/.claude/projects/<id>/` folder |
| `--output DIR` | Output directory (default: `.usage/` in cwd) |
| `--json` | Also write `report.json` |
| `--prices FILE` | JSON file with custom pricing (see [Updating Prices](#updating-prices)) |
| `--update-prices` | Write an editable pricing template to `~/.config/cc-usage/prices.json` and exit |
| `--quiet` | Suppress progress output |

### Examples

```bash
# Current project, default output
cc-usage

# Another project (works with spaces and special chars in path)
cc-usage --project "~/CoWork/My Project (v2)"

# Explicit sessions dir + JSON output
cc-usage --sessions-dir ~/.claude/projects/C--Users-me-myproject --json

# Refresh the editable pricing template, then run
cc-usage --update-prices
cc-usage
```

## Output Files

| File | Contents |
|------|----------|
| `report.md` | Human-readable Markdown summary |
| `detail.csv` | One row per API call (includes `cache_write_5m_tokens`, `cache_write_1h_tokens`, `inference_geo`, `service_tier`, `geo_multiplier`) |
| `by_session.csv` | Aggregated per session |
| `by_day.csv` | Aggregated per calendar day |
| `by_model.csv` | Aggregated per model |
| `report.json` | All tables as JSON (requires `--json`) |

## How It Works

Claude Code writes a JSONL file per session to `~/.claude/projects/<encoded-cwd>/`.  
Each assistant turn contains a `usage` object with token counts for every billing category.  
`cc-usage` reads these files locally and computes cost using Anthropic's published pricing.

### Token Categories Tracked

| Field in JSONL | Tracked as | Notes |
|----------------|-----------|-------|
| `input_tokens` | `input_tokens` | Standard prompt tokens |
| `cache_creation.ephemeral_5m_input_tokens` | `cache_write_5m_tokens` | 5-minute cache write |
| `cache_creation.ephemeral_1h_input_tokens` | `cache_write_1h_tokens` | 1-hour cache write (higher rate) |
| `cache_read_input_tokens` | `cache_read_tokens` | Cache hits / refreshes |
| `output_tokens` | `output_tokens` | Generated tokens |
| `inference_geo` | `inference_geo` | Regional routing; triggers 1.1x surcharge if set |
| `service_tier` | `service_tier` | `standard` or `fast` |
| `server_tool_use.web_search_requests` | `web_searches` | |
| `server_tool_use.web_fetch_requests` | `web_fetches` | |

### Pricing

Source: [platform.claude.com/docs/en/about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing)

| Model | Input | Cache Write 5m | Cache Write 1h | Cache Read | Output |
|-------|------:|---------------:|---------------:|-----------:|-------:|
| claude-opus-4-7/4-6/4-5 | $5.00 | $6.25 | $10.00 | $0.50 | $25.00 |
| claude-opus-4-1 / claude-opus-4 | $15.00 | $18.75 | $30.00 | $1.50 | $75.00 |
| claude-sonnet-4 (all variants) | $3.00 | $3.75 | $6.00 | $0.30 | $15.00 |
| claude-haiku-4-5 | $1.00 | $1.25 | $2.00 | $0.10 | $5.00 |
| claude-haiku-3-5 | $0.80 | $1.00 | $1.60 | $0.08 | $4.00 |
| claude-3-haiku | $0.25 | $0.30 | $0.50 | $0.03 | $1.25 |

All prices are USD per million tokens. Unknown models fall back to Sonnet 4 rates.  
A **1.1x data-residency surcharge** is applied per API call when `inference_geo` is set to a specific region (not `global`).

## Updating Prices

When Anthropic updates their pricing, run:

```bash
cc-usage --update-prices
```

This writes the current built-in rates to `~/.config/cc-usage/prices.json` as an editable template:

```json
{
  "as_of": "2026-04-25",
  "source": "https://platform.claude.com/docs/en/about-claude/pricing",
  "prices": {
    "claude-sonnet-4": {
      "input": 3.00,
      "cache_write_5m": 3.75,
      "cache_write_1h": 6.00,
      "cache_read": 0.30,
      "output": 15.00
    }
  }
}
```

Edit `as_of` and any rates you need to change — omit models you don't want to override.  
The file is auto-loaded on every run once it exists.

To use a one-off prices file without writing to the config:

```bash
cc-usage --prices ./my-prices.json
```

## Adding to a Project

Add to `.gitignore`:

```
.usage/
```

Then run `cc-usage` whenever you want a fresh report.
