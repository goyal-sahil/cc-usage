"""cc-usage — CLI entry point."""

import argparse
import sys
from pathlib import Path

from .detect import sessions_dir_for
from .loader import load_rows
from . import aggregate as agg
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
        help="Explicit path to the Claude Code sessions directory "
             "(skips auto-detection).",
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
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output.",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

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
        print(f"Reading {len(jsonl_files)} session files from {sessions_dir} …")

    rows = load_rows(sessions_dir)
    if not rows:
        sys.exit("No assistant usage records found.")

    if not args.quiet:
        print(f"  {len(rows):,} API calls in {len(set(r['session_id'] for r in rows))} sessions")

    # ── aggregate ────────────────────────────────────────────────────────────
    sessions = agg.by_session(rows)
    days = agg.by_day(rows)
    models = agg.by_model(rows)
    detail = agg.detail(rows)

    totals = {
        "sessions": len(sessions),
        "api_calls": sum(b["api_calls"] for b in sessions),
        "input_tokens": sum(b["input_tokens"] for b in sessions),
        "cache_write_tokens": sum(b["cache_write_tokens"] for b in sessions),
        "cache_read_tokens": sum(b["cache_read_tokens"] for b in sessions),
        "output_tokens": sum(b["output_tokens"] for b in sessions),
        "total_tokens": sum(b["total_tokens"] for b in sessions),
        "cost_usd": round(sum(b["cost_usd"] for b in sessions), 6),
        "cache_savings_usd": round(sum(b["cache_savings_usd"] for b in sessions), 6),
        "web_searches": sum(b["web_searches"] for b in sessions),
        "web_fetches": sum(b["web_fetches"] for b in sessions),
    }

    # ── write ────────────────────────────────────────────────────────────────
    write_csvs(out_dir, detail, sessions, days, models)
    write_markdown(out_dir, sessions_dir, sessions, days, models, totals)
    if args.json:
        write_json(out_dir, sessions, days, models, totals)

    if not args.quiet:
        files = "detail.csv  by_session.csv  by_day.csv  by_model.csv  report.md"
        if args.json:
            files += "  report.json"
        print(f"\nOutput -> {out_dir}/")
        print(f"  {files}")
        print(f"\nTotal cost (est.):  ${totals['cost_usd']:.4f}")
        print(f"Total tokens:       {totals['total_tokens']:,}")
        print(f"Cache savings:      ${totals['cache_savings_usd']:.4f}")


if __name__ == "__main__":
    main()
