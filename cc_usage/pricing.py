"""Token pricing tables (USD per million tokens)."""

import json
from pathlib import Path

PRICES_AS_OF = "2025-01-01"

_BUILTIN: dict[str, dict[str, float]] = {
    "claude-opus-4":   {"input": 15.00, "cache_write": 18.75, "cache_read": 1.50, "output": 75.00},
    "claude-sonnet-4": {"input":  3.00, "cache_write":  3.75, "cache_read": 0.30, "output": 15.00},
    "claude-haiku-4":  {"input":  0.80, "cache_write":  1.00, "cache_read": 0.08, "output":  4.00},
    "claude-3-5-sonnet": {"input": 3.00, "cache_write": 3.75, "cache_read": 0.30, "output": 15.00},
    "claude-3-5-haiku":  {"input": 0.80, "cache_write": 1.00, "cache_read": 0.08, "output":  4.00},
    "claude-3-opus":     {"input": 15.00, "cache_write": 18.75, "cache_read": 1.50, "output": 75.00},
}

_DEFAULT: dict[str, float] = {"input": 3.00, "cache_write": 3.75, "cache_read": 0.30, "output": 15.00}

# Active prices — may be replaced by load_user_prices()
_PRICES: dict[str, dict[str, float]] = dict(_BUILTIN)

# Ordered list used for the report table (reflects active prices)
PRICES_TABLE: list[tuple[str, dict[str, float]]] = []


def _rebuild_table() -> None:
    PRICES_TABLE.clear()
    for prefix, rates in _PRICES.items():
        PRICES_TABLE.append((prefix, rates))


_rebuild_table()

# Path checked automatically unless --prices is passed
USER_PRICES_PATH = Path.home() / ".config" / "cc-usage" / "prices.json"


def load_user_prices(path: Path | None = None) -> str | None:
    """
    Load user-supplied prices from a JSON file, merging into the active table.
    Returns the resolved path string on success, None if no file was found.

    File format:
    {
      "as_of": "2025-06-01",          // optional — updates PRICES_AS_OF
      "prices": {
        "claude-sonnet-4": {
          "input": 3.00,
          "cache_write": 3.75,
          "cache_read": 0.30,
          "output": 15.00
        }
      }
    }
    """
    global PRICES_AS_OF

    target = path or USER_PRICES_PATH
    if not target.exists():
        return None

    with open(target, encoding="utf-8") as f:
        data = json.load(f)

    if "as_of" in data:
        PRICES_AS_OF = data["as_of"]

    for prefix, rates in data.get("prices", {}).items():
        _PRICES[prefix] = {**_BUILTIN.get(prefix, _DEFAULT), **rates}

    _rebuild_table()
    return str(target)


def get_price(model: str, kind: str) -> float:
    model = model or ""
    for prefix, rates in _PRICES.items():
        if model.startswith(prefix):
            return rates.get(kind, _DEFAULT[kind])
    return _DEFAULT[kind]


def token_cost(tokens: int, model: str, kind: str) -> float:
    return tokens / 1_000_000 * get_price(model, kind)
