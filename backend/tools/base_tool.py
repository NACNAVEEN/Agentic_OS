"""
Tool Abstraction Layer — Base Interface

All tools (mock and future real) implement this interface.
Agents interact only with BaseTool — they never know if data is mocked or real.
Swapping MockAssetTool → BACnetAssetTool requires ZERO agent code changes.

New in this version:
  - parameters_schema: JSON Schema for each tool's inputs
  - _validate_params(): validates LLM-generated params before execution
  - Module-level _CACHE: prevents re-reading JSON from disk on every call
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ── Module-level data cache (avoids repeated disk reads) ──────────────────────
_CACHE: dict[str, Any] = {}


def clear_cache() -> None:
    """Clear the tool data cache. Useful for testing."""
    _CACHE.clear()


class ToolResult(BaseModel):
    """Standardised tool execution result — same shape for mock and real tools."""
    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0
    parameters: dict = {}


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    Future real API tools inherit this same interface — zero agent changes needed.
    """

    def __init__(self):
        self._name = self.__class__.__name__

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name used in LLM prompts and tool registry."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for LLM context."""

    @property
    def parameters_schema(self) -> dict:
        """
        JSON Schema for this tool's parameters.
        Override in subclasses to enable input validation.
        Example:
            {
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string", "description": "Asset identifier"},
                },
                "required": ["asset_id"],
            }
        """
        return {"type": "object", "properties": {}}

    @abstractmethod
    def _execute(self, **kwargs) -> Any:
        """Internal execution logic — override in subclasses."""

    def _validate_params(self, **kwargs) -> dict:
        """
        Validate and filter kwargs against parameters_schema.
        Unknown keys are dropped (prevents LLM hallucinated params from reaching _execute).
        Missing optional keys receive their default values.
        """
        schema_props = self.parameters_schema.get("properties", {})
        if not schema_props:
            return kwargs  # No schema defined — pass through

        validated: dict = {}
        for key, value in kwargs.items():
            if key in schema_props:
                validated[key] = value
            else:
                logger.debug("Tool %s: dropping unknown param '%s'", self.name, key)

        # Apply defaults for missing optional fields
        for key, prop in schema_props.items():
            if key not in validated and "default" in prop:
                validated[key] = prop["default"]

        return validated

    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool: validate params → run → wrap result with timing."""
        start = time.time()
        try:
            validated = self._validate_params(**kwargs)
            data = self._execute(**validated)
            elapsed = (time.time() - start) * 1000
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                execution_time_ms=round(elapsed, 2),
                parameters=validated,
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error("Tool %s execution failed: %s", self.name, e, exc_info=True)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                execution_time_ms=round(elapsed, 2),
                parameters=kwargs,
            )
