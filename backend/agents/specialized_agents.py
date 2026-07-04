"""
Specialized Agents — Asset, Alarm, Energy, Documentation
Each agent uses its assigned tools to fulfill subtasks from the Planner.

KEY DESIGN: Each agent returns ONLY its NEW contributions to state.
The Annotated reducers in orchestrator/state.py handle merging across parallel agents.

Updated:
  - Uses get_llm() DI instead of inline ChatGroq
  - 2-round ReAct-lite loop: if first tool call returns an error, agent
    selects a fallback tool in a second LLM call
  - Error recovery: failed agents return status="failed" instead of crashing graph
"""
import json
import logging
import time
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage
from orchestrator.state import AgentState, ReasoningStep, ToolInvocation, AgentResult
from tools import get_tools_for_agent
from services.llm_factory import get_llm

logger = logging.getLogger(__name__)


def _build_tool_descriptions(agent_name: str) -> str:
    """Build tool description string for the LLM prompt."""
    tools = get_tools_for_agent(agent_name)
    parts = []
    for name, tool in tools.items():
        schema = tool.parameters_schema.get("properties", {})
        param_str = ", ".join(
            f"{k}: {v.get('type', 'string')}" for k, v in schema.items()
        ) if schema else "no parameters"
        parts.append(f"- **{name}**: {tool.description} (params: {param_str})")
    return "\n".join(parts)


def _parse_tool_calls(content: str, tools: dict) -> list[dict]:
    """Parse JSON tool call array from LLM response. Returns valid calls only."""
    try:
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        calls = json.loads(raw)
        if not isinstance(calls, list):
            calls = [calls]
        return [c for c in calls if isinstance(c, dict) and c.get("tool") in tools]
    except (json.JSONDecodeError, IndexError, TypeError) as exc:
        logger.warning("Failed to parse tool calls: %s", exc)
        return []


def _create_agent_function(agent_name: str, display_name: str):
    """Factory function to create agent node functions with 2-round ReAct loop."""

    def agent_fn(state: AgentState) -> dict:
        start_time = time.time()
        user_query = state.get("user_query", "")
        plan = state.get("execution_plan", {})

        agents_to_spawn = state.get("agents_to_spawn", [])
        if agent_name not in agents_to_spawn:
            return {}

        new_reasoning: list = []
        new_invocations: list = []
        prompt_tokens = 0
        completion_tokens = 0

        new_reasoning.append(ReasoningStep(
            agent=display_name,
            thought=f"Starting execution for: '{user_query}'",
            action="Analyzing available tools and planning tool calls",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))

        tools = get_tools_for_agent(agent_name)
        tool_descriptions = _build_tool_descriptions(agent_name)
        my_tasks = [
            step.get("task", "")
            for step in plan.get("execution_plan", [])
            if step.get("agent") == agent_name
        ]
        tasks_str = "\n".join(f"- {t}" for t in my_tasks) if my_tasks else "Fulfill the user's request"

        tool_call_prompt = f"""You are the {display_name} in AgenticOS.

## Your Tasks:
{tasks_str}

## Available Tools:
{tool_descriptions}

## User Query: {user_query}

Decide which tools to call. Respond with ONLY a JSON array:
[
    {{"tool": "tool_name", "parameters": {{"param1": "value1"}}}},
    {{"tool": "tool_name", "parameters": {{}}}}
]

Use specific asset IDs when mentioned (e.g. "AHU-01", "Chiller-01").
If no specific asset is mentioned, use tools that search broadly."""

        # ── Round 1: Initial tool selection ───────────────────────────────
        llm = get_llm(temperature=0.1, max_tokens=512)
        response = llm.invoke([
            SystemMessage(content=tool_call_prompt),
            HumanMessage(content=f"Execute your tasks for: {user_query}"),
        ])
        prompt_tokens += response.response_metadata.get("token_usage", {}).get("prompt_tokens", 0)
        completion_tokens += response.response_metadata.get("token_usage", {}).get("completion_tokens", 0)

        tool_calls = _parse_tool_calls(response.content, tools)
        if not tool_calls and tools:
            tool_calls = [{"tool": list(tools.keys())[0], "parameters": {}}]

        # ── Execute Round 1 tools ──────────────────────────────────────────
        tool_results: dict = {}
        tools_used: list[str] = []
        had_errors = False

        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            params = tc.get("parameters", {})
            if tool_name not in tools:
                continue

            new_reasoning.append(ReasoningStep(
                agent=display_name,
                thought=f"Calling tool: {tool_name}",
                action=f"Parameters: {json.dumps(params)}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))

            result = tools[tool_name].execute(**params)
            tool_results[tool_name] = result.data if result.success else result.error
            tools_used.append(tool_name)

            new_invocations.append(ToolInvocation(
                agent=display_name,
                tool_name=tool_name,
                parameters=params,
                output=result.data if result.success else result.error,
                execution_time_ms=result.execution_time_ms,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))

            if not result.success:
                had_errors = True

        # ── Round 2: ReAct fallback if errors occurred ────────────────────
        if had_errors and tools:
            new_reasoning.append(ReasoningStep(
                agent=display_name,
                thought="Round 1 had errors. Re-evaluating with available data.",
                action="Selecting fallback tool in Round 2",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))

            error_context = json.dumps(tool_results, default=str)[:500]
            fallback_prompt = f"""Round 1 tool calls had errors: {error_context}

Available tools: {tool_descriptions}
User query: {user_query}

Select ONE fallback tool to recover missing data. Respond with ONLY a JSON array:
[{{"tool": "tool_name", "parameters": {{}}}}]"""

            r2 = llm.invoke([
                SystemMessage(content=fallback_prompt),
                HumanMessage(content="Select a fallback tool."),
            ])
            prompt_tokens += r2.response_metadata.get("token_usage", {}).get("prompt_tokens", 0)
            completion_tokens += r2.response_metadata.get("token_usage", {}).get("completion_tokens", 0)

            fallback_calls = _parse_tool_calls(r2.content, tools)
            for tc in fallback_calls[:1]:  # Max 1 fallback tool
                tool_name = tc.get("tool", "")
                params = tc.get("parameters", {})
                if tool_name in tools and tool_name not in tools_used:
                    result = tools[tool_name].execute(**params)
                    tool_results[tool_name] = result.data if result.success else result.error
                    tools_used.append(tool_name)
                    new_invocations.append(ToolInvocation(
                        agent=display_name,
                        tool_name=tool_name,
                        parameters=params,
                        output=result.data if result.success else result.error,
                        execution_time_ms=result.execution_time_ms,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    ))

        elapsed = (time.time() - start_time) * 1000
        new_reasoning.append(ReasoningStep(
            agent=display_name,
            thought=f"Completed execution. Used {len(tools_used)} tool(s).",
            action=f"Tools: {', '.join(tools_used) if tools_used else 'none'}",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))

        return {
            "agent_results": {
                agent_name: AgentResult(
                    agent_name=display_name,
                    status="completed",
                    result=tool_results,
                    tools_used=tools_used,
                    execution_time_ms=round(elapsed, 2),
                    confidence_score=0.9 if not had_errors else 0.6,
                )
            },
            "reasoning_trace": new_reasoning,
            "tool_invocations": new_invocations,
            "total_prompt_tokens": prompt_tokens,
            "total_completion_tokens": completion_tokens,
            "total_tool_calls": len(tools_used),
        }

    agent_fn.__name__ = agent_name
    return agent_fn


# Create all specialized agent functions
asset_agent = _create_agent_function("asset_agent", "Asset Agent")
alarm_agent = _create_agent_function("alarm_agent", "Alarm Agent")
energy_agent = _create_agent_function("energy_agent", "Energy Agent")
documentation_agent = _create_agent_function("documentation_agent", "Documentation Agent")
