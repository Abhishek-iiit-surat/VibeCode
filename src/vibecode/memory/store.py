"""
MemoryStore: the persistent Memory piece of the agent architecture.

Reads prior conversation state on startup, writes it back after every turn,
and auto-compacts (summarize-and-trim) once the conversation grows past a
size threshold — a DIY equivalent of Claude Code's own memory auto-compaction,
implemented as one extra Claude call rather than relying on the Anthropic
beta server-side compaction feature (avoids a beta-header dependency here).
"""

import json
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(".vibecode") / "memory.json"
DEFAULT_CHAR_THRESHOLD = 60_000
KEEP_RECENT_MESSAGES = 6


def _to_plain(value: Any) -> Any:
    """Recursively convert Anthropic SDK content blocks to plain JSON-able values."""
    if hasattr(value, "model_dump"):
        return _to_plain(value.model_dump())
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    return value


class MemoryStore:
    def __init__(self, path: Path = DEFAULT_PATH):
        self.path = Path(path)

    def load(self) -> list:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            return []

    def save(self, messages: list) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(_to_plain(messages), indent=2))

    def should_compact(self, messages: list, char_threshold: int = DEFAULT_CHAR_THRESHOLD) -> bool:
        return len(json.dumps(_to_plain(messages))) > char_threshold

    def compact(self, messages: list, client, model: str, keep_recent: int = KEEP_RECENT_MESSAGES) -> list:
        if len(messages) <= keep_recent:
            return messages

        to_summarize = _to_plain(messages[:-keep_recent])
        recent = _to_plain(messages[-keep_recent:])

        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system="Summarize this conversation history concisely, preserving any "
                   "decisions, file paths, and unfinished work a continuation would need.",
            messages=[
                {"role": "user", "content": json.dumps(to_summarize)},
            ],
        )
        summary_text = next((b.text for b in response.content if b.type == "text"), "")

        compacted = [{"role": "user", "content": f"[Earlier conversation summary]\n{summary_text}"}]
        compacted.extend(recent)
        return compacted
