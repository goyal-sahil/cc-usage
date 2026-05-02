# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-05-02

### Fixed
- **Multi-model session/day costs were wildly wrong.** `aggregate._sum_bucket`
  summed tokens across all rows in a session/day bucket, then priced the bucket
  against a single model — whichever appeared on the **last row** in iteration
  order. When a session mixed Haiku, Sonnet, and Opus calls (the common case),
  totals could swing 5× across runs of the same growing JSONL. Cost is now
  computed **per row** using the row's own model and `geo_multiplier`, then
  summed into buckets. Verified against Claude API billing: $2.83 reported vs.
  $2.83 actual on the regression dataset (previously fluctuated $1.34 → $11.50
  → $2.73 across three runs).
- **API calls were double-counted.** Claude Code emits one JSONL entry per
  content block (thinking, text, tool_use, …) but every entry carries the same
  response-level `usage` payload. The loader now deduplicates by
  `message.id`, so each API call contributes exactly once. On the regression
  dataset this drops the call count from 112 logged entries to 54 actual API
  calls.
- **`geo_multiplier` was dropped in aggregates.** It was captured per row by
  the loader and applied in `detail()`, but `_enrich()` ignored it. Aggregates
  now include the data-residency surcharge.

### Changed
- `model` field in `by_session.csv` and `by_day.csv` now reports `"mixed"`
  when a session/day spans more than one model, instead of an arbitrary
  last-row model name.

### Added
- `--version` CLI flag.
- `.test-data/` added to `.gitignore`.

## [0.1.0] - Initial release

- CLI for analysing Claude Code token usage from local JSONL session files.
- Per-session, per-day, per-model, and per-call breakdowns as CSV / Markdown / JSON.
- Built-in pricing table with user override via `~/.config/cc-usage/prices.json`
  or `--prices FILE`; `--update-prices` writes an editable template.
- Split 5m / 1h cache pricing.
- Data-residency geo surcharge (1.1x) applied per call when `inference_geo`
  names a specific region.

[0.2.0]: https://github.com/goyal-sahil/cc-usage/releases/tag/v0.2.0
[0.1.0]: https://github.com/goyal-sahil/cc-usage/releases/tag/v0.1.0
