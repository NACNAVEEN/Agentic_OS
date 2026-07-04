"""
AgentState — Shared state for LangGraph orchestration.
This TypedDict flows through all nodes in the graph.

Updated:
  - verification_result: dict — populated by VerificationAgent
  - session_id: str — for MemorySaver thread keying
  - AgentResult now includes confidence_score
"""
from typing import TypedDict, Annotated, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class ToolInvocation(TypedDict):
    """Record of a single tool invocation."""
    agent: str
    tool_name: str
    parameters: dict
    output: Any
    execution_time_ms: float
    timestamp: str


class ReasoningStep(TypedDict):
    """A single step in an agent's reasoning chain."""
    agent: str
    thought: str
    action: str
    timestamp: str


class AgentResult(TypedDict):
    """Result from a specialized agent."""
    agent_name: str
    status: str              # created | running | completed | failed
    result: Any
    tools_used: list[str]
    execution_time_ms: float
    confidence_score: float  # 0.0–1.0, how confident the agent is in its data


def _merge_dicts(a: dict, b: dict) -> dict:
    """Merge two dicts — used to combine agent_results from parallel agents."""
    return {**a, **b}


def _concat_lists(a: list, b: list) -> list:
    """Concatenate two lists — accumulate traces from parallel agents."""
    return a + b


def _sum_ints(a: int, b: int) -> int:
    """Sum two ints — accumulate token counts from parallel agents."""
    return a + b


class AgentState(TypedDict):
    """The shared state flowing through the LangGraph."""
    # Chat messages (auto-accumulated by LangGraph)
    messages: Annotated[list[BaseMessage], add_messages]

    # Session identity (used by MemorySaver for conversation continuity)
    session_id: str

    # User's original query
    user_query: str

    # Planner output
    execution_plan: dict
    agents_to_spawn: list[str]

    # Agent execution results — merged across parallel agents
    agent_results: Annotated[dict[str, AgentResult], _merge_dicts]

    # Observability traces — accumulated across parallel agents
    reasoning_trace: Annotated[list[ReasoningStep], _concat_lists]
    tool_invocations: Annotated[list[ToolInvocation], _concat_lists]

    # Token tracking — summed across parallel agents
    total_prompt_tokens: Annotated[int, _sum_ints]
    total_completion_tokens: Annotated[int, _sum_ints]
    total_tool_calls: Annotated[int, _sum_ints]

    # Supervisor output
    final_response: str

    # Verification Agent output — added AFTER supervisor
    verification_result: dict
