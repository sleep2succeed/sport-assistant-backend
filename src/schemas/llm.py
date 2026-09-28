from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class OpenAIRoles(StrEnum):
    """OpenAI API message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class OpenAIRequestMessage(BaseModel):
    """OpenAI-compatible request message."""

    role: OpenAIRoles = OpenAIRoles.SYSTEM
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize to the exact shape the OpenAI API expects."""
        data: dict[str, Any] = {"role": str(self.role)}
        if self.content is not None:
            data["content"] = self.content
        if self.tool_calls is not None:
            data["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            data["tool_call_id"] = self.tool_call_id
        return data

