"""
WebSearchTool: resolves a natural-language query to candidate URLs.

Uses the Tavily Search API (api.tavily.com) rather than scraping a search
engine's HTML — DuckDuckGo's html.duckduckgo.com blocks scripted requests
with an anti-bot challenge page, so scraping isn't reliable. Tavily's free
tier (1,000 credits/month) covers personal/light use at $0; TAVILY_API_KEY
must be set in .env.
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from vibecode.tools.base import Tool, ToolResult

SEARCH_URL = "https://api.tavily.com/search"
TIMEOUT_SECONDS = 10
MAX_RESULTS = 8


class WebSearchTool(Tool):
    """Search the web for a natural-language query and return candidate URLs."""

    name = "web_search"
    description = (
        "Search the web for a natural-language query. Returns up to "
        f"{MAX_RESULTS} candidate results, each with a URL, title, and short "
        "snippet. Use this to find relevant pages, then fetch the promising "
        "ones with web_fetch to read their full content."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query."},
        },
        "required": ["query"],
    }

    def execute(self, query: str) -> ToolResult:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return ToolResult(content="TAVILY_API_KEY is not set — add it to .env.", is_error=True)

        payload = json.dumps({"api_key": api_key, "query": query, "max_results": MAX_RESULTS}).encode("utf-8")
        request = Request(SEARCH_URL, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            return ToolResult(content=f"HTTP {e.code} searching for '{query}': {e.read().decode(errors='ignore')}", is_error=True)
        except URLError as e:
            return ToolResult(content=f"Failed to search for '{query}': {e.reason}", is_error=True)
        except TimeoutError:
            return ToolResult(content=f"Timed out searching for '{query}'", is_error=True)

        results = data.get("results", [])
        if not results:
            return ToolResult(content=f"No results for '{query}'.")

        lines = [
            f"{i}. {r.get('title', '(untitled)')}\n   {r.get('url', '')}\n   {r.get('content', '')[:300]}"
            for i, r in enumerate(results, start=1)
        ]
        return ToolResult(content="\n".join(lines))
