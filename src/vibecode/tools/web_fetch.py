"""
WebFetchTool: fetches a URL and returns its content as Markdown.

Plain stdlib HTTP GET (no cost beyond the network request) piped through
markdownify for HTML->Markdown conversion, so the subagent reading the
result gets real structure (headings, links, lists) instead of a flattened
text blob.
"""

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from markdownify import markdownify

from vibecode.tools.base import Tool, ToolResult

USER_AGENT = "Mozilla/5.0 (compatible; VibeCodeBot/1.0)"
TIMEOUT_SECONDS = 10
MAX_CHARS = 20_000
# markdownify's `strip` only drops the tag, not its text content, so
# <script>/<style>/<svg> bodies would otherwise leak raw JS/CSS/markup into
# the "readable" output — remove those elements outright before converting.
DROP_TAGS = ["script", "style", "svg", "noscript", "template"]


class WebFetchTool(Tool):
    """Fetch a URL and return its content as Markdown, truncated to a safe size."""

    name = "web_fetch"
    description = (
        "Fetch a URL over HTTP(S) and return its page content converted to "
        "Markdown. Use this to read the full content of a specific page you "
        "already have the URL for (e.g. from web_search results). Not a "
        "search engine — you need the exact URL."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to fetch, including scheme (e.g. 'https://...')."},
        },
        "required": ["url"],
    }

    def execute(self, url: str) -> ToolResult:
        if not url.lower().startswith(("http://", "https://")):
            return ToolResult(content=f"Refusing to fetch non-http(s) URL: {url}", is_error=True)

        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                content_type = response.headers.get_content_type()
                raw = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="ignore")
        except HTTPError as e:
            return ToolResult(content=f"HTTP {e.code} fetching {url}: {e.reason}", is_error=True)
        except URLError as e:
            return ToolResult(content=f"Failed to fetch {url}: {e.reason}", is_error=True)
        except TimeoutError:
            return ToolResult(content=f"Timed out fetching {url}", is_error=True)

        if content_type == "text/html":
            soup = BeautifulSoup(raw, "html.parser")
            for element in soup(DROP_TAGS):
                element.decompose()
            text = markdownify(str(soup)).strip()
        else:
            text = raw

        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + f"\n… (truncated, {len(text) - MAX_CHARS} more characters)"

        return ToolResult(content=text or "(empty page)")
