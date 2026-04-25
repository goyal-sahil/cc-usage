"""Render aggregated data as Markdown and CSV files."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .pricing import PRICES_TABLE, _DEFAULT


# ── CSV ──────────────────────────────────────────────────────────────────────

_DETAIL_FIELDS = [
    "timestamp", "session_id", "model", "api_calls",
    "input_tokens", "cache_write_tokens", "cache_read_tokens",
    "output_tokens", "total_tokens", "cost_usd", "cache_savings_usd",
    "web_searches", "web_fetches",
]
_SESSION_FIELDS = [
    "session_id", "date", "model", "api_calls",
    "input_tokens", "cache_write_tokens", "cache_read_tokens",
    "output_tokens", "total_tokens", "cost_usd", "cache_savings_usd",
    "web_searches", "web_fetches",
]
_DAY_FIELDS = [
    "date", "api_calls",
    "input_tokens", "cache_write_tokens", "cache_read_tokens",
    "output_tokens", "total_tokens", "cost_usd", "cache_savings_usd",
    "web_searches", "web_fetches",
]
_MODEL_FIELDS = [
    "model", "api_calls",
    "input_tokens", "cache_write_tokens", "cache_read_tokens",
    "output_tokens", "total_tokens", "cost_usd", "cache_savings_usd",
]


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_csvs(out_dir: Path, detail, sessions, days, models) -> None:
    _write_csv(out_dir / "detail.csv", _DETAIL_FIELDS, detail)
    _write_csv(out_dir / "by_session.csv", _SESSION_FIELDS, sessions)
    _write_csv(out_dir / "by_day.csv", _DAY_FIELDS, days)
    _write_csv(out_dir / "by_model.csv", _MODEL_FIELDS, models)


# ── JSON ─────────────────────────────────────────────────────────────────────

def write_json(out_dir: Path, sessions, days, models, totals: dict) -> None:
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "totals": totals,
        "by_model": models,
        "by_day": days,
        "by_session": sessions,
    }
    (out_dir / "report.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


# ── Markdown ─────────────────────────────────────────────────────────────────

def write_markdown(
    out_dir: Path,
    sessions_dir: Path,
    sessions: list[dict],
    days: list[dict],
    models: list[dict],
    totals: dict,
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Claude Code Usage Report",
        "",
        f"Generated: {now}  ",
        f"Sessions: `{sessions_dir}`",
        "",
        "## Totals",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Sessions | {totals['sessions']:,} |",
        f"| API calls | {totals['api_calls']:,} |",
        f"| Input tokens | {totals['input_tokens']:,} |",
        f"| Cache write tokens | {totals['cache_write_tokens']:,} |",
        f"| Cache read tokens | {totals['cache_read_tokens']:,} |",
        f"| Output tokens | {totals['output_tokens']:,} |",
        f"| **Total tokens** | **{totals['total_tokens']:,}** |",
        f"| **Est. cost (USD)** | **${totals['cost_usd']:.2f}** |",
        f"| Cache savings (est.) | ${totals['cache_savings_usd']:.2f} |",
        f"| Web searches | {totals['web_searches']:,} |",
        f"| Web fetches | {totals['web_fetches']:,} |",
        "",
        "## By Model",
        "",
        "| Model | Calls | Input | Cache Write | Cache Read | Output | Cost USD |",
        "|-------|------:|------:|------------:|-----------:|-------:|---------:|",
    ]
    for b in models:
        lines.append(
            f"| {b['model']} | {b['api_calls']:,} | {b['input_tokens']:,} | "
            f"{b['cache_write_tokens']:,} | {b['cache_read_tokens']:,} | "
            f"{b['output_tokens']:,} | ${b['cost_usd']:.2f} |"
        )

    lines += [
        "",
        "## By Day",
        "",
        "| Date | Calls | Total Tokens | Cost USD | Cache Savings |",
        "|------|------:|-------------:|---------:|--------------:|",
    ]
    for b in days:
        lines.append(
            f"| {b['date']} | {b['api_calls']:,} | {b['total_tokens']:,} | "
            f"${b['cost_usd']:.2f} | ${b['cache_savings_usd']:.2f} |"
        )

    lines += [
        "",
        "## By Session",
        "",
        "| Session | Date | Model | Calls | Total Tokens | Cost USD |",
        "|---------|------|-------|------:|-------------:|---------:|",
    ]
    for b in sessions:
        short = b["session_id"][:8] + "…"
        lines.append(
            f"| `{short}` | {b['date']} | {b['model']} | {b['api_calls']:,} | "
            f"{b['total_tokens']:,} | ${b['cost_usd']:.2f} |"
        )

    lines += [
        "",
        "## Pricing Reference (USD per million tokens)",
        "",
        "| Model | Input | Cache Write | Cache Read | Output |",
        "|-------|------:|------------:|-----------:|-------:|",
    ]
    for prefix, r in PRICES_TABLE:
        lines.append(
            f"| {prefix} | ${r['input']:.2f} | ${r['cache_write']:.2f} | ${r['cache_read']:.2f} | ${r['output']:.2f} |"
        )
    lines.append(
        f"| *(default / unknown)* | ${_DEFAULT['input']:.2f} | ${_DEFAULT['cache_write']:.2f} | ${_DEFAULT['cache_read']:.2f} | ${_DEFAULT['output']:.2f} |"
    )

    lines += [
        "",
        "## Output Files",
        "",
        "| File | Contents |",
        "|------|----------|",
        "| `detail.csv` | One row per API call |",
        "| `by_session.csv` | Aggregated per session |",
        "| `by_day.csv` | Aggregated per calendar day |",
        "| `by_model.csv` | Aggregated per model |",
        "| `report.json` | All tables as JSON (if `--json`) |",
    ]

    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
