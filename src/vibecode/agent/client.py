"""
Model client setup for the VibeCode agent loop.

litellm.completion() is a plain function, not a client object with state —
it reads provider API keys straight from the environment on every call. We
still load .env here (once, at import time) so ANTHROPIC_API_KEY /
OPENAI_API_KEY are in os.environ before the first completion() call, and
still hand a `client` value through the codebase (run_agent_loop, hooks,
sub-agents, memory compaction) so call sites don't need to change — it's
just the litellm module itself now, not a per-provider SDK instance.
"""

import os

import litellm
from dotenv import load_dotenv

load_dotenv()
DEFAULT_MODEL = "openai/gpt-5.4-mini"
SUBAGENT_MODEL = "openai/gpt-4.1-mini"


def get_client():
    """Validate credentials are present and return the litellm module as the
    shared `client` value passed through the rest of the app."""
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "No provider API key set."
            "ANTHROPIC_API_KEY and/or OPENAI_API_KEY."
        )
    return litellm
