"""
PricingTracker: accumulates the API cost of a query across every model call —
the main agent loop and every nested sub-agent loop it spawns via Task — and
reports the total once the query finishes processing.

This isn't a Hook (hooks/base.py) because it doesn't wrap tool calls; it wraps
model calls, which happen inside run_agent_loop right after
client.completion(). run_agent_loop invokes on_usage(model, usage) after
every response it gets back (usage already normalized by
agent.response.normalize_usage — plain input/output/cache_read/cache_write
token counts, provider-agnostic), main loop or sub-agent loop alike, so a
single tracker instance passed through to both sees the full picture.
"""

from dataclasses import dataclass, field

# USD per million tokens: (input, output, cache_write, cache_read). Update
# this table if pricing changes or a new model is added — it's intentionally
# the only place rates are hardcoded. Keyed by the litellm model id
# (provider-prefixed) since that's what run_agent_loop passes through.
RATES_PER_MILLION = {
    "anthropic/claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30},
    "anthropic/claude-haiku-4-5": {"input": 1.00, "output": 5.00, "cache_write": 1.25, "cache_read": 0.10},
    # cache_write is unused for OpenAI (no explicit cache-write charge); cache_read
    # follows OpenAI's standard ~25%-of-input discount for prompt caching.
    "openai/gpt-5.4-mini": {"input": 0.75, "output": 4.50, "cache_write": 0.0, "cache_read": 0.1875},
    "openai/gpt-4.1-mini": {"input": 0.40, "output": 1.60, "cache_write": 0.0, "cache_read": 0.10},
}


@dataclass
class _ModelTotals:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    calls: int = 0

    def cost(self, model: str) -> float:
        rates = RATES_PER_MILLION.get(model)
        if rates is None:
            return 0.0
        return (
            self.input_tokens * rates["input"]
            + self.output_tokens * rates["output"]
            + self.cache_write_tokens * rates["cache_write"]
            + self.cache_read_tokens * rates["cache_read"]
        ) / 1_000_000


@dataclass
class PricingTracker:
    _by_model: dict = field(default_factory=dict)

    def on_usage(self, model: str, usage: dict) -> None:
        totals = self._by_model.setdefault(model, _ModelTotals())
        totals.input_tokens += usage.get("input_tokens", 0) or 0
        totals.output_tokens += usage.get("output_tokens", 0) or 0
        totals.cache_write_tokens += usage.get("cache_write_tokens", 0) or 0
        totals.cache_read_tokens += usage.get("cache_read_tokens", 0) or 0
        totals.calls += 1

    def total_cost(self) -> float:
        return sum(totals.cost(model) for model, totals in self._by_model.items())

    def reset(self) -> None:
        self._by_model.clear()

    def summary(self) -> str:
        if not self._by_model:
            return "No API calls made."

        lines = []
        for model, totals in self._by_model.items():
            lines.append(
                f"  {model}: {totals.calls} call(s), "
                f"{totals.input_tokens:,} in / {totals.output_tokens:,} out tokens"
                + (
                    f", {totals.cache_read_tokens:,} cache-read"
                    if totals.cache_read_tokens
                    else ""
                )
                + f" — ${totals.cost(model):.4f}"
            )
        lines.append(f"  total: ${self.total_cost():.4f}")
        return "\n".join(lines)
