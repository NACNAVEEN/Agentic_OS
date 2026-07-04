"""
Planner Agent — Understands user intent, decomposes tasks, decides which agents to spawn.
This is the ENTRY POINT of the orchestration graph.

Updated: uses get_llm() DI instead of inline ChatGroq instantiation.
         Logs a warning (not silent fallback) when JSON parsing fails.
"""
import json
import logging
import time
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage
from orchestrator.state import AgentState, ReasoningStep
from services.llm_factory import get_llm

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are the Planner Agent in an Operations Intelligence Platform (AgenticOS).
Your job is to understand the user's request and create an execution plan.

## Available Specialized Agents:
1. **asset_agent** — Retrieves asset information, hierarchy, metadata, equipment relationships
   - Tools: get_asset, search_assets, get_related_assets
   - Use when: User asks about specific equipment, asset details, or equipment relationships

2. **alarm_agent** — Investigates alarms, correlation analysis, root cause analysis
   - Tools: get_active_alarms, get_alarm_history, correlate_alarms
   - Use when: User asks about alarms, alerts, faults, or wants investigation of issues

3. **energy_agent** — Energy consumption analysis, trends, peak demand, cost estimation
   - Tools: get_energy_data, get_consumption_trend, get_peak_demand
   - Use when: User asks about energy usage, consumption, costs, or efficiency

4. **documentation_agent** — Retrieves technical documents, SOPs, manuals, maintenance guides
   - Tools: search_documents, retrieve_sop
   - Use when: User asks about procedures, protocols, standards, manuals, or technical knowledge

## Critical Rules:
- ONLY spawn agents that are NECESSARY for the user's request
- For simple knowledge questions (e.g., "What is BACnet?"), spawn ONLY the documentation_agent
- For alarm investigations, you typically need: alarm_agent + asset_agent (and sometimes documentation_agent for SOPs)
- For comprehensive diagnostics, you may need multiple agents
- NEVER spawn all agents unless the query truly requires all of them

## Output Format:
You MUST respond with ONLY a valid JSON object (no markdown, no explanation):
{
    "understanding": "Your understanding of the user's request",
    "execution_plan": [
        {"step": 1, "task": "Description of subtask", "agent": "agent_name"},
        {"step": 2, "task": "Description of subtask", "agent": "agent_name"}
    ],
    "agents_to_spawn": ["agent_name1", "agent_name2"],
    "reasoning": "Why you chose these specific agents"
}
"""


def planner_agent(state: AgentState) -> dict:
    """Planner Agent node — analyzes intent and creates execution plan."""
    start_time = time.time()

    user_query = state.get("user_query", "")
    new_reasoning: list[ReasoningStep] = []

    new_reasoning.append(ReasoningStep(
        agent="Planner Agent",
        thought=f"Analyzing user request: '{user_query}'",
        action="Understanding intent and determining required agents",
        timestamp=datetime.now(timezone.utc).isoformat(),
    ))

    # ── LLM call via DI factory ───────────────────────────────────────────
    llm = get_llm(temperature=0.1, max_tokens=1024)
    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=f"User Request: {user_query}"),
    ]
    response = llm.invoke(messages)

    prompt_tokens = response.response_metadata.get("token_usage", {}).get("prompt_tokens", 0)
    completion_tokens = response.response_metadata.get("token_usage", {}).get("completion_tokens", 0)

    # ── Parse JSON plan ───────────────────────────────────────────────────
    plan_data = None
    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        plan_data = json.loads(content)
    except (json.JSONDecodeError, IndexError) as exc:
        logger.warning(
            "Planner failed to parse JSON response (falling back to documentation_agent). "
            "Raw content: %r — Error: %s",
            response.content[:200],
            exc,
        )
        plan_data = {
            "understanding": user_query,
            "execution_plan": [{"step": 1, "task": "Search documentation", "agent": "documentation_agent"}],
            "agents_to_spawn": ["documentation_agent"],
            "reasoning": "Unable to parse structured plan — defaulting to documentation search.",
        }

    agents_to_spawn = plan_data.get("agents_to_spawn", ["documentation_agent"])

    new_reasoning.append(ReasoningStep(
        agent="Planner Agent",
        thought=plan_data.get("reasoning", "Plan created"),
        action=f"Spawning agents: {', '.join(agents_to_spawn)}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    ))

    return {
        "execution_plan": plan_data,
        "agents_to_spawn": agents_to_spawn,
        "reasoning_trace": new_reasoning,
        "total_prompt_tokens": prompt_tokens,
        "total_completion_tokens": completion_tokens,
    }
