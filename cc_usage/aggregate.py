"""Aggregate raw rows into session / day / model buckets."""

from collections import defaultdict
from .pricing import token_cost


def _empty():
    return defaultdict(int)


def _sum_bucket(rows: list[dict], key_fn) -> dict[str, dict]:
    buckets: dict[str, defaultdict] = {}
    for r in rows:
        k = key_fn(r)
        if k not in buckets:
            buckets[k] = _empty()
        b = buckets[k]
        b["input_tokens"] += r["input_tokens"]
        b["cache_write_tokens"] += r["cache_write_tokens"]
        b["cache_read_tokens"] += r["cache_read_tokens"]
        b["output_tokens"] += r["output_tokens"]
        b["web_searches"] += r["web_searches"]
        b["web_fetches"] += r["web_fetches"]
        b["api_calls"] += 1
        b["_model"] = r["model"]
    return {k: dict(v) for k, v in buckets.items()}


def _enrich(bucket: dict, model: str | None = None) -> dict:
    m = model or bucket.pop("_model", "unknown")
    bucket["model"] = m
    bucket["total_tokens"] = (
        bucket["input_tokens"] + bucket["cache_write_tokens"] +
        bucket["cache_read_tokens"] + bucket["output_tokens"]
    )
    bucket["cost_usd"] = round(
        token_cost(bucket["input_tokens"], m, "input") +
        token_cost(bucket["cache_write_tokens"], m, "cache_write") +
        token_cost(bucket["cache_read_tokens"], m, "cache_read") +
        token_cost(bucket["output_tokens"], m, "output"),
        6,
    )
    bucket["cache_savings_usd"] = round(
        token_cost(bucket["cache_read_tokens"], m, "input") -
        token_cost(bucket["cache_read_tokens"], m, "cache_read"),
        6,
    )
    return bucket


def by_session(rows: list[dict]) -> list[dict]:
    buckets = _sum_bucket(rows, lambda r: r["session_id"])
    result = []
    for sid, b in buckets.items():
        dates = [r["date"] for r in rows if r["session_id"] == sid and r["date"]]
        b["session_id"] = sid
        b["date"] = min(dates) if dates else ""
        _enrich(b)
        result.append(b)
    return sorted(result, key=lambda b: b["date"])


def by_day(rows: list[dict]) -> list[dict]:
    buckets = _sum_bucket(rows, lambda r: r["date"])
    result = []
    for d, b in buckets.items():
        b["date"] = d
        _enrich(b)
        result.append(b)
    return sorted(result, key=lambda b: b["date"])


def by_model(rows: list[dict]) -> list[dict]:
    buckets = _sum_bucket(rows, lambda r: r["model"])
    result = []
    for m, b in buckets.items():
        _enrich(b, model=m)
        result.append(b)
    return sorted(result, key=lambda b: -b["cost_usd"])


def detail(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        d = dict(r)
        d["api_calls"] = 1
        _enrich(d, model=d["model"])
        out.append(d)
    return out
