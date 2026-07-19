"""
ToolRegistry: holds the set of tools available to a reasoning loop (either the
main Agent or a Sub-Agent with a restricted subset) and dispatches calls to them.

Every entry is a "client tool" (a Tool instance) — VibeCode executes it
itself (FileRead, FileWrite, Bash, Task). There is no server-tool concept
anymore: that only existed for Anthropic-executed tools like web_search,
which litellm can't run server-side the same way for other providers, so
support for it was dropped along with the Anthropic-only client.
"""

from vibecode.tools.base import Tool, ToolResult


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def is_client_tool(self, name: str) -> bool:
        return name in self._tools

    def list_schemas(self) -> list[dict]:
        """All tool schemas in the shape litellm.completion()'s `tools=[...]` expects."""
        return [t.to_openai_schema() for t in self._tools.values()]

    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, name: str, tool_input: dict) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(content=f"Unknown tool: {name}", is_error=True)
        try:
            return tool.execute(**tool_input)
        except Exception as e:
            return ToolResult(content=f"Tool '{name}' raised an error: {e}", is_error=True)

    def subset(self, names: list[str]) -> "ToolRegistry":
        """A new registry exposing only the named tools — used to hand a
        restricted tool set to a sub-agent."""
        restricted = ToolRegistry()
        for name in names:
            if name in self._tools:
                restricted.register(self._tools[name])
        return restricted
