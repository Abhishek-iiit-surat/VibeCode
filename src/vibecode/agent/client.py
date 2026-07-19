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

# LiteLLM model identifiers: "<provider>/<model>". Swapping DEFAULT_MODEL
# to an "openai/..." id is the whole story for switching providers — no
# other code names a provider explicitly.
DEFAULT_MODEL = "anthropic/claude-sonnet-4-6"
# Sub-agents always run on this model regardless of what the main agent uses —
# delegated subtasks are narrower in scope, so the cheaper/faster model is the
# right default rather than inheriting the parent's model.
SUBAGENT_MODEL = "anthropic/claude-haiku-4-5"


def get_client():
    """Validate credentials are present and return the litellm module as the
    shared `client` value passed through the rest of the app."""
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "No provider API key set. Copy .env.example to .env and add "
            "ANTHROPIC_API_KEY and/or OPENAI_API_KEY."
        )
    return litellm
