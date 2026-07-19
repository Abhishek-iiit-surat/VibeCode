"""
Base interfaces that every VibeCode tool implements.

Tools are the things the Agent reasoning loop can call: FileRead, FileWrite,
Bash, etc. Each tool describes itself with a name/description/JSON-schema
triple (the same shape Claude's tool-use API expects) and knows how to
execute itself given the arguments Claude supplied.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolResult:
    """The outcome of executing a tool, fed back to the model as a tool_result block."""
    content: str
    is_error: bool = False


class Tool(ABC):
    """A single callable capability exposed to the Agent reasoning loop."""

    name: str
    description: str
    input_schema: dict

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Run the tool with the arguments Claude provided and return the result."""
        raise NotImplementedError

    def to_openai_schema(self) -> dict:
        """The dict shape litellm.completion()'s `tools` list expects — the
        OpenAI function-calling wrapper. litellm translates this into
        whatever the target provider (Anthropic, OpenAI, ...) needs."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }
