"""Token pricing tables (USD per million tokens)."""

_PRICES: dict[str, dict[str, float]] = {
    "claude-opus-4":   {"input": 15.00, "cache_write": 18.75, "cache_read": 1.50, "output": 75.00},
    "claude-sonnet-4": {"input":  3.00, "cache_write":  3.75, "cache_read": 0.30, "output": 15.00},
    "claude-haiku-4":  {"input":  0.80, "cache_write":  1.00, "cache_read": 0.08, "output":  4.00},
    # legacy
    "claude-3-5-sonnet": {"input": 3.00, "cache_write": 3.75, "cache_read": 0.30, "output": 15.00},
    "claude-3-5-haiku":  {"input": 0.80, "cache_write": 1.00, "cache_read": 0.08, "output":  4.00},
    "claude-3-opus":     {"input": 15.00, "cache_write": 18.75, "cache_read": 1.50, "output": 75.00},
}

_DEFAULT: dict[str, float] = {"input": 3.00, "cache_write": 3.75, "cache_read": 0.30, "output": 15.00}


PRICES_TABLE: list[tuple[str, dict[str, float]]] = [
    ("claude-opus-4",     {"input": 15.00, "cache_write": 18.75, "cache_read": 1.50, "output": 75.00}),
    ("claude-sonnet-4",   {"input":  3.00, "cache_write":  3.75, "cache_read": 0.30, "output": 15.00}),
    ("claude-haiku-4",    {"input":  0.80, "cache_write":  1.00, "cache_read": 0.08, "output":  4.00}),
    ("claude-3-5-sonnet", {"input":  3.00, "cache_write":  3.75, "cache_read": 0.30, "output": 15.00}),
    ("claude-3-5-haiku",  {"input":  0.80, "cache_write":  1.00, "cache_read": 0.08, "output":  4.00}),
    ("claude-3-opus",     {"input": 15.00, "cache_write": 18.75, "cache_read": 1.50, "output": 75.00}),
]


def get_price(model: str, kind: str) -> float:
    model = model or ""
    for prefix, rates in _PRICES.items():
        if model.startswith(prefix):
            return rates.get(kind, _DEFAULT[kind])
    return _DEFAULT[kind]


def token_cost(tokens: int, model: str, kind: str) -> float:
    return tokens / 1_000_000 * get_price(model, kind)
