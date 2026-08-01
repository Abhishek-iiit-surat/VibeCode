"""
Mem0Store: selective-recall alternative to MemoryStore (store.py).

MemoryStore keeps one running summary and replays it whole on every query —
cheap, but a fact from 20 queries ago is only as good as how well it survived
repeated re-summarization. Mem0Store instead keeps memories as discrete,
independently retrievable entries in a local vector store (Qdrant, on-disk)
and pulls back only the entries relevant to the current task via similarity
search, so specific facts don't degrade as the project grows.

Local/self-hosted mem0 (the `Memory` class, not `MemoryClient`) — no mem0.ai
account or API key needed. Still calls OpenAI for embeddings (text-embedding-3-small)
regardless of which model the agent itself is using, since that's the only
embedder configured below; OPENAI_API_KEY must be set for that reason alone
even on an Anthropic-model run
"""

import os
from pathlib import Path
from typing import Any

from mem0 import Memory

from vibecode.agent.client import DEFAULT_MODEL

# How many past facts mem0.search() pulls into context per query. Override via
# .env — MEM0_RECALL_LIMIT=10 — rather than editing code when tuning recall
# breadth vs. prompt size.
DEFAULT_RECALL_LIMIT = int(os.getenv("MEM0_RECALL_LIMIT", "5"))


class Mem0Store:
    def __init__(self, project_root: Path, user_id: str = "default"):
        self.user_id = user_id
        qdrant_path = str(Path(project_root) / ".vibecode" / "mem0_qdrant")
        self._mem = Memory.from_config(
            {
                # avoids mem0's default gpt-5-mini, which rejects mem0's default temperature=0.1;
                # DEFAULT_MODEL (not SUBAGENT_MODEL) because extraction needs to follow mem0's
                # nested JSON schema reliably, which the smaller subagent model didn't do
                "llm": {
                    "provider": "litellm",
                    "config": {"model": DEFAULT_MODEL, "temperature": 1, "is_reasoning_model": False},
                },
                "embedder": {"provider": "openai", "config": {"model": "text-embedding-3-small"}},
                "vector_store": {
                    "provider": "qdrant",
                    "config": {"path": qdrant_path, "collection_name": "vibecode_memory"},
                },
            }
        )

    def load(self, query: str, limit: int = DEFAULT_RECALL_LIMIT) -> list:
        """Return the messages relevant to `query` as a single primed user
        message, or [] if nothing relevant has been stored yet."""
        results = self._mem.search(query, filters={"user_id": self.user_id}, top_k=limit).get("results", [])
        if not results:
            return []
        facts = "\n".join(f"- {r['memory']}" for r in results)
        return [{"role": "user", "content": f"[Relevant memory]\n{facts}"}]

    def clear(self) -> None:
        """Wipe every stored memory for this user (irreversible)."""
        self._mem.delete_all(user_id=self.user_id)

    def add_summary(self, summary: str) -> None:
        """Store a pre-condensed summary directly (e.g. a whole session's
        summary from SessionStore), bypassing per-query extraction — the
        text is already distilled, so mem0's own extraction call would be
        redundant here."""
        if summary.strip():
            self._mem.add([{"role": "user", "content": summary}], user_id=self.user_id)

    def finalize(self, messages: list, client: Any, model: str) -> None:
        """Call once a query has finished. Lets mem0 extract and store
        whatever facts are worth keeping from this exchange — no manual
        summarization call needed, mem0 does its own extraction LLM call
        internally via `add()`."""
        plain = [
            {"role": m["role"], "content": m.get("content") or ""}
            for m in messages
            if m.get("role") in ("user", "assistant") and m.get("content")
        ]
        if plain:
            self._mem.add(plain, user_id=self.user_id)
