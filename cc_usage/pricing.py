"""Token pricing tables (USD per million tokens).

Source: https://platform.claude.com/docs/en/about-claude/pricing
"""

import json
from datetime import date
from pathlib import Path

PRICES_AS_OF = "2026-04-25"

# Ordered list — most-specific prefix first so startswith matching is correct.
_BUILTIN: list[tuple[str, dict[str, float]]] = [
    # Opus 4.x  (4.7 / 4.6 / 4.5 are cheaper than original Opus 4)
    ("claude-opus-4-7",   {"input":  5.00, "cache_write_5m":  6.25, "cache_write_1h": 10.00, "cache_read": 0.50, "output": 25.00}),
    ("claude-opus-4-6",   {"input":  5.00, "cache_write_5m":  6.25, "cache_write_1h": 10.00, "cache_read": 0.50, "output": 25.00}),
    ("claude-opus-4-5",   {"input":  5.00, "cache_write_5m":  6.25, "cache_write_1h": 10.00, "cache_read": 0.50, "output": 25.00}),
    ("claude-opus-4-1",   {"input": 15.00, "cache_write_5m": 18.75, "cache_write_1h": 30.00, "cache_read": 1.50, "output": 75.00}),
    ("claude-opus-4",     {"input": 15.00, "cache_write_5m": 18.75, "cache_write_1h": 30.00, "cache_read": 1.50, "output": 75.00}),
    # Sonnet 4.x  (all variants share the same rate)
    ("claude-sonnet-4",   {"input":  3.00, "cache_write_5m":  3.75, "cache_write_1h":  6.00, "cache_read": 0.30, "output": 15.00}),
    # Haiku 4.x
    ("claude-haiku-4-5",  {"input":  1.00, "cache_write_5m":  1.25, "cache_write_1h":  2.00, "cache_read": 0.10, "output":  5.00}),
    ("claude-haiku-4",    {"input":  1.00, "cache_write_5m":  1.25, "cache_write_1h":  2.00, "cache_read": 0.10, "output":  5.00}),
    # Legacy claude-3.x models
    ("claude-3-7-sonnet", {"input":  3.00, "cache_write_5m":  3.75, "cache_write_1h":  6.00, "cache_read": 0.30, "output": 15.00}),
    ("claude-3-5-sonnet", {"input":  3.00, "cache_write_5m":  3.75, "cache_write_1h":  6.00, "cache_read": 0.30, "output": 15.00}),
    ("claude-3-5-haiku",  {"input":  0.80, "cache_write_5m":  1.00, "cache_write_1h":  1.60, "cache_read": 0.08, "output":  4.00}),
    ("claude-3-opus",     {"input": 15.00, "cache_write_5m": 18.75, "cache_write_1h": 30.00, "cache_read": 1.50, "output": 75.00}),
    ("claude-3-haiku",    {"input":  0.25, "cache_write_5m":  0.30, "cache_write_1h":  0.50, "cache_read": 0.03, "output":  1.25}),
]

_DEFAULT: dict[str, float] = {
    "input": 3.00, "cache_write_5m": 3.75, "cache_write_1h": 6.00,
    "cache_read": 0.30, "output": 15.00,
}

# Active prices — may be extended/overridden by load_user_prices()
_PRICES: list[tuple[str, dict[str, float]]] = list(_BUILTIN)

# Flat view for the report table
PRICES_TABLE: list[tuple[str, dict[str, float]]] = []


def _rebuild_table() -> None:
    PRICES_TABLE.clear()
    PRICES_TABLE.extend(_PRICES)


_rebuild_table()

USER_PRICES_PATH = Path.home() / ".config" / "cc-usage" / "prices.json"


def get_rates(model: str) -> dict[str, float]:
    model = model or ""
    for prefix, rates in _PRICES:
        if model.startswith(prefix):
            return rates
    return _DEFAULT


def token_cost_bucket(bucket: dict, model: str) -> float:
    """Compute USD cost for an aggregated token bucket."""
    r = get_rates(model)
    return (
        bucket.get("input_tokens", 0)          / 1e6 * r["input"] +
        bucket.get("cache_write_5m_tokens", 0) / 1e6 * r["cache_write_5m"] +
        bucket.get("cache_write_1h_tokens", 0) / 1e6 * r["cache_write_1h"] +
        bucket.get("cache_read_tokens", 0)     / 1e6 * r["cache_read"] +
        bucket.get("output_tokens", 0)         / 1e6 * r["output"]
    )


def load_user_prices(path: Path | None = None) -> str | None:
    """
    Merge user-supplied prices into the active table.
    Returns the resolved path string on success, None if no file found.

    File format:
    {
      "as_of": "2026-01-01",
      "prices": {
        "claude-sonnet-4": {
          "input": 3.00, "cache_write_5m": 3.75, "cache_write_1h": 6.00,
          "cache_read": 0.30, "output": 15.00
        }
      }
    }
    Omit any key to keep the built-in value.
    """
    global PRICES_AS_OF

    target = path or USER_PRICES_PATH
    if not target.exists():
        return None

    with open(target, encoding="utf-8") as f:
        data = json.load(f)

    if "as_of" in data:
        PRICES_AS_OF = data["as_of"]

    for prefix, overrides in data.get("prices", {}).items():
        # Find and update existing entry, or prepend a new one
        builtin_rates = next((r for p, r in _BUILTIN if p == prefix), dict(_DEFAULT))
        merged = {**builtin_rates, **overrides}
        for i, (p, _) in enumerate(_PRICES):
            if p == prefix:
                _PRICES[i] = (prefix, merged)
                break
        else:
            _PRICES.insert(0, (prefix, merged))

    _rebuild_table()
    return str(target)


def update_prices(path: Path | None = None) -> str:
    """
    Write the current built-in pricing to the user config file as an editable template.
    Run this to initialise or refresh the file, then edit as_of / rates as needed.
    """
    target = path or USER_PRICES_PATH
    target.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "as_of": str(date.today()),
        "source": "https://platform.claude.com/docs/en/about-claude/pricing",
        "_note": "Edit 'as_of' and any rates below. Omit models you don't want to override.",
        "prices": {prefix: dict(rates) for prefix, rates in _BUILTIN},
    }
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(target)
