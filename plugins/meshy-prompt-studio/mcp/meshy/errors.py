"""Shared errors for Meshy Prompt Studio."""

from __future__ import annotations

from typing import Any


class MeshyError(Exception):
    """Error type returned through MCP tool calls."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"message": self.message}
        if self.status_code is not None:
            payload["status_code"] = self.status_code
        if self.details is not None:
            payload["details"] = self.details
        return payload
