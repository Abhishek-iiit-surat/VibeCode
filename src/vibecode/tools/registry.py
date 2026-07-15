"""
ToolRegistry: holds the set of tools available to a reasoning loop (either the
main Agent or a Sub-Agent with a restricted subset) and dispatches calls to them.

Two kinds of entries live here:
- "client tools" (Tool instances) — VibeCode executes these itself (FileRead,
  FileWrite, Bash, Task).
- "server tools" (raw schema dicts) — Anthropic executes these server-side
  (e.g. web_search). They're included in the schemas sent to the API but the
  loop never calls .execute() on them; Claude returns their results inline.
"""

from vibecode.tools.base import Tool, ToolResult


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._server_tool_schemas: dict[str, dict] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def register_server_tool(self, schema: dict) -> None:
        """Register a raw Anthropic server-tool schema (e.g. web_search_20260209)."""
        self._server_tool_schemas[schema["name"]] = schema

    def is_client_tool(self, name: str) -> bool:
        return name in self._tools

    def list_schemas(self) -> list[dict]:
        """All tool schemas (client + server) in the shape `tools=[...]` expects."""
        return [t.to_anthropic_schema() for t in self._tools.values()] + list(
            self._server_tool_schemas.values()
        )

    def tool_names(self) -> list[str]:
        return list(self._tools.keys()) + list(self._server_tool_schemas.keys())

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
            elif name in self._server_tool_schemas:
                restricted.register_server_tool(self._server_tool_schemas[name])
        return restricted
