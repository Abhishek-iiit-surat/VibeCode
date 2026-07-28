"""
SessionStore: one CLI process = one session, archived on exit.

Distinct from Mem0Store: Mem0Store extracts granular, independently
retrievable facts per query (via similarity search). SessionStore instead
keeps a coarse, chronological log of whole sessions — each one condensed to
a single summary and appended to a sliding-window JSON file on disk (oldest
dropped past WINDOW_SIZE). A new process's in-memory conversation always
starts empty; the archive is not auto-replayed into context. The same
summary is also added into Mem0Store so future similarity search can still
surface facts from past sessions.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WINDOW_SIZE = 5

SUMMARY_SYSTEM_PROMPT = (
    "Summarize this coding session concisely: what was asked, what was done, "
    "any decisions or facts (file paths, names, choices made) worth recalling "
    "in a future session. A few sentences is enough for a short session."
)


class SessionStore:
    def __init__(self, project_root: Path):
        self._path = Path(project_root) / ".vibecode" / "sessions.json"
        self._queries: list[dict] = []

    def record(self, task: str, response: str) -> None:
        """Call once per completed query during the session."""
        self._queries.append({"task": task, "response": response})

    def save(self, client: Any, model: str, memory: Any = None) -> None:
        """Call once at process exit. No-op if no queries happened this
        session — an empty session isn't worth archiving. Also feeds the
        summary into `memory` (a Mem0Store), if given, so future sessions
        can still recall it via similarity search."""
        if not self._queries:
            return

        summary = self._summarize(client, model)
        session_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "query_count": len(self._queries),
        }

        sessions = self._load_sessions()
        sessions.append(session_entry)
        sessions = sessions[-WINDOW_SIZE:]

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(sessions, indent=2), encoding="utf-8")

        if memory is not None:
            memory.add_summary(summary)

    def _summarize(self, client: Any, model: str) -> str:
        from vibecode.agent.response import normalize_response

        transcript = "\n\n".join(
            f"User: {q['task']}\nAssistant: {q['response']}" for q in self._queries
        )
        response = client.completion(
            model=model,
            max_tokens=512,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": transcript},
            ],
        )
        return normalize_response(response).text

    def _load_sessions(self) -> list[dict]:
        if not self._path.exists():
            return []
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
