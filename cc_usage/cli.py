"""cc-usage — CLI entry point."""

import argparse
import sys
from pathlib import Path

from .detect import sessions_dir_for
from .loader import load_rows
from . import aggregate as agg
from .pricing import load_user_prices, update_prices
from .report import write_csvs, write_json, write_markdown


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cc-usage",
        description="Analyse Claude Code token usage from local JSONL session files.",
    )
    source = p.add_mutually_exclusive_group()
    source.add_argument(
        "--project", "-p",
        metavar="DIR",
        help="Project directory to analyse (default: current working directory). "
             "cc-usage resolves the matching ~/.claude/projects/<encoded>/ automatically.",
    )
    source.add_argument(
        "--sessions-dir", "-s",
        metavar="DIR",
        help="Explicit path to the Claude Code sessions directory (skips auto-detection).",
    )
    p.add_argument(
        "--output", "-o",
        metavar="DIR",
        default=".usage",
        help="Directory for output files (default: .usage/ inside the project dir).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Also write report.json alongside the CSVs.",
    )
    p.add_argument(
        "--prices",
        metavar="FILE",
        help="JSON file with custom pricing (overrides built-in rates). "
             "Auto-loaded from ~/.config/cc-usage/prices.json if present.",
    )
    p.add_argument(
        "--update-prices",
        action="store_true",
        help="Write the current built-in pricing to ~/.config/cc-usage/prices.json "
             "as an editable template, then exit. "
             "Verify rates at: https://platform.claude.com/docs/en/about-claude/pricing",
    )
    p.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output.",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    # ── --update-prices: write template and exit ─────────────────────────────
    if args.update_prices:
        path = update_prices()
        print(f"Pricing template written to {path}")
        print("Edit 'as_of' and any rates, then re-run cc-usage.")
        print("Reference: https://platform.claude.com/docs/en/about-claude/pricing")
        return

    # ── load pricing (auto or explicit) ─────────────────────────────────────
    prices_file = Path(args.prices) if args.prices else None
    prices_source = load_user_prices(prices_file)
    if not args.quiet and prices_source:
        print(f"Prices loaded from {prices_source}")

    # ── resolve sessions dir ─────────────────────────────────────────────────
    if args.sessions_dir:
        sessions_dir = Path(args.sessions_dir)
    else:
        project = Path(args.project) if args.project else None
        sessions_dir = sessions_dir_for(project)

    if not sessions_dir.exists():
        sys.exit(
            f"Sessions directory not found: {sessions_dir}\n"
            "Run from inside a Claude Code project, or pass --project / --sessions-dir."
        )

    jsonl_files = list(sessions_dir.glob("*.jsonl"))
    if not jsonl_files:
        sys.exit(f"No .jsonl files found in {sessions_dir}")

    # ── resolve output dir ───────────────────────────────────────────────────
    out_dir = Path(args.output)
    if not out_dir.is_absolute() and args.project:
        out_dir = Path(args.project) / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── parse ────────────────────────────────────────────────────────────────
    if not args.quiet:
        print(f"Reading {len(jsonl_files)} session files from {sessions_dir} ...")

    rows = load_rows(sessions_dir)
    if not rows:
        sys.exit("No assistant usage records found.")

    if not args.quiet:
        print(f"  {len(rows):,} API calls in {len(set(r['session_id'] for r in rows))} sessions")

    # ── aggregate ────────────────────────────────────────────────────────────
    sessions = agg.by_session(rows)
    days     = agg.by_day(rows)
    models   = agg.by_model(rows)
    det      = agg.detail(rows)

    totals = {
        "sessions":              len(sessions),
        "api_calls":             sum(b["api_calls"]             for b in sessions),
        "input_tokens":          sum(b["input_tokens"]          for b in sessions),
        "cache_write_5m_tokens": sum(b["cache_write_5m_tokens"] for b in sessions),
        "cache_write_1h_tokens": sum(b["cache_write_1h_tokens"] for b in sessions),
        "cache_read_tokens":     sum(b["cache_read_tokens"]     for b in sessions),
        "output_tokens":         sum(b["output_tokens"]         for b in sessions),
        "total_tokens":          sum(b["total_tokens"]          for b in sessions),
        "cost_usd":              round(sum(b["cost_usd"]            for b in sessions), 6),
        "cache_savings_usd":     round(sum(b["cache_savings_usd"]   for b in sessions), 6),
        "web_searches":          sum(b["web_searches"]          for b in sessions),
        "web_fetches":           sum(b["web_fetches"]           for b in sessions),
    }

    # ── write ────────────────────────────────────────────────────────────────
    write_csvs(out_dir, det, sessions, days, models)
    write_markdown(out_dir, sessions_dir, sessions, days, models, totals, prices_source)
    if args.json:
        write_json(out_dir, sessions, days, models, totals)

    if not args.quiet:
        files = "detail.csv  by_session.csv  by_day.csv  by_model.csv  report.md"
        if args.json:
            files += "  report.json"
        print(f"\nOutput -> {out_dir}/")
        print(f"  {files}")
        print(f"\nTotal cost (est.):  ${totals['cost_usd']:.2f}")
        print(f"Total tokens:       {totals['total_tokens']:,}")
        print(f"Cache savings:      ${totals['cache_savings_usd']:.2f}")


if __name__ == "__main__":
    main()
