"""Aggregate raw rows into session / day / model buckets."""

from collections import defaultdict
from .pricing import get_rates, token_cost_bucket


def _empty() -> dict:
    b: dict = defaultdict(int)
    b["cost_usd"] = 0.0
    b["cache_savings_usd"] = 0.0
    b["_models"] = set()
    return b


def _row_cost(r: dict) -> tuple[float, float]:
    """Cost and cache-savings for a single row, using that row's own model and geo."""
    m = r["model"]
    rates = get_rates(m)
    cost = token_cost_bucket(r, m) * r.get("geo_multiplier", 1.0)
    savings = r["cache_read_tokens"] / 1e6 * (rates["input"] - rates["cache_read"])
    return cost, savings


def _sum_bucket(rows: list[dict], key_fn) -> dict[str, dict]:
    buckets: dict[str, dict] = {}
    for r in rows:
        k = key_fn(r)
        if k not in buckets:
            buckets[k] = _empty()
        b = buckets[k]
        b["input_tokens"]          += r["input_tokens"]
        b["cache_write_5m_tokens"] += r["cache_write_5m_tokens"]
        b["cache_write_1h_tokens"] += r["cache_write_1h_tokens"]
        b["cache_read_tokens"]     += r["cache_read_tokens"]
        b["output_tokens"]         += r["output_tokens"]
        b["web_searches"]          += r["web_searches"]
        b["web_fetches"]           += r["web_fetches"]
        b["api_calls"]             += 1
        cost, savings = _row_cost(r)
        b["cost_usd"]              += cost
        b["cache_savings_usd"]     += savings
        b["_models"].add(r["model"])
    return {k: dict(v) for k, v in buckets.items()}


def _enrich(bucket: dict, model: str | None = None) -> dict:
    models = bucket.pop("_models", set())
    if model is not None:
        bucket["model"] = model
    elif len(models) == 1:
        bucket["model"] = next(iter(models))
    elif models:
        bucket["model"] = "mixed"
    else:
        bucket["model"] = "unknown"
    bucket["cache_write_tokens"] = bucket["cache_write_5m_tokens"] + bucket["cache_write_1h_tokens"]
    bucket["total_tokens"] = (
        bucket["input_tokens"] +
        bucket["cache_write_tokens"] +
        bucket["cache_read_tokens"] +
        bucket["output_tokens"]
    )
    bucket["cost_usd"] = round(bucket["cost_usd"], 6)
    bucket["cache_savings_usd"] = round(bucket["cache_savings_usd"], 6)
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
        d["cache_write_tokens"] = d["cache_write_5m_tokens"] + d["cache_write_1h_tokens"]
        d["total_tokens"] = (
            d["input_tokens"] + d["cache_write_tokens"] +
            d["cache_read_tokens"] + d["output_tokens"]
        )
        d["cost_usd"] = round(token_cost_bucket(d, d["model"]) * d.get("geo_multiplier", 1.0), 6)
        rates = get_rates(d["model"])
        cr = d["cache_read_tokens"]
        d["cache_savings_usd"] = round(cr / 1e6 * (rates["input"] - rates["cache_read"]), 6)
        out.append(d)
    return out
