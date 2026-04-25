"""Parse Claude Code JSONL session files into usage rows."""

import json
from pathlib import Path


def load_rows(sessions_dir: Path) -> list[dict]:
    """
    Read all *.jsonl in sessions_dir.
    Returns one dict per assistant API call that contains usage data.
    """
    rows = []
    for path in sorted(sessions_dir.glob("*.jsonl")):
        session_id = path.stem
        with open(path, encoding="utf-8", errors="replace") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "assistant":
                    continue
                msg = obj.get("message", {})
                usage = msg.get("usage")
                if not usage:
                    continue
                ts = obj.get("timestamp", "")
                rows.append({
                    "session_id": session_id,
                    "timestamp": ts,
                    "date": ts[:10] if ts else "",
                    "model": msg.get("model", "unknown"),
                    "input_tokens": usage.get("input_tokens", 0),
                    "cache_write_tokens": usage.get("cache_creation_input_tokens", 0),
                    "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "web_searches": usage.get("server_tool_use", {}).get("web_search_requests", 0),
                    "web_fetches": usage.get("server_tool_use", {}).get("web_fetch_requests", 0),
                })
    return rows
