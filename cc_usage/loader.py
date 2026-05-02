"""Parse Claude Code JSONL session files into usage rows."""

import json
from pathlib import Path

# inference_geo values that are standard global routing (no surcharge)
_GEO_NO_SURCHARGE = {"", "global"}


def load_rows(sessions_dir: Path) -> list[dict]:
    """
    Read all *.jsonl in sessions_dir.
    Returns one dict per assistant API call that contains usage data.
    """
    rows = []
    # Claude Code emits one JSONL entry per content block (thinking, text,
    # tool_use, ...) but every entry carries the same response-level usage
    # payload. Dedupe by message id so we count each API call exactly once.
    seen_msg_ids: set[str] = set()
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
                msg_id = msg.get("id")
                if msg_id:
                    if msg_id in seen_msg_ids:
                        continue
                    seen_msg_ids.add(msg_id)

                # Cache creation tokens split by TTL (present in newer API responses)
                cache_creation = usage.get("cache_creation", {})
                cache_write_5m = cache_creation.get(
                    "ephemeral_5m_input_tokens",
                    # Fallback: older responses have only the aggregate field
                    usage.get("cache_creation_input_tokens", 0)
                    if not cache_creation else 0,
                )
                cache_write_1h = cache_creation.get("ephemeral_1h_input_tokens", 0)

                # Data-residency geo surcharge: 1.1x when a specific region is set
                geo = usage.get("inference_geo", "")
                geo_multiplier = 1.1 if geo not in _GEO_NO_SURCHARGE else 1.0

                ts = obj.get("timestamp", "")
                rows.append({
                    "session_id":          session_id,
                    "timestamp":           ts,
                    "date":                ts[:10] if ts else "",
                    "model":               msg.get("model", "unknown"),
                    "input_tokens":        usage.get("input_tokens", 0),
                    "cache_write_5m_tokens": cache_write_5m,
                    "cache_write_1h_tokens": cache_write_1h,
                    "cache_read_tokens":   usage.get("cache_read_input_tokens", 0),
                    "output_tokens":       usage.get("output_tokens", 0),
                    "geo_multiplier":      geo_multiplier,
                    "inference_geo":       geo,
                    "service_tier":        usage.get("service_tier", ""),
                    "web_searches":        usage.get("server_tool_use", {}).get("web_search_requests", 0),
                    "web_fetches":         usage.get("server_tool_use", {}).get("web_fetch_requests", 0),
                })
    return rows
