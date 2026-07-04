"""
LangGraph Orchestrator — The core state machine routing through agents.

Flow: Planner → [Asset, Alarm, Energy, Documentation] (conditional, parallel)
      → Supervisor → Verification → END

Updated:
  - verification node added after supervisor
  - MemorySaver checkpointer for conversation continuity
  - Error recovery: agent exceptions caught, return failed status
"""
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from orchestrator.state import AgentState
from agents import (
    planner_agent,
    asset_agent,
    alarm_agent,
    energy_agent,
    documentation_agent,
    supervisor_agent,
    verification_agent,
)

logger = logging.getLogger(__name__)


def _safe_agent(agent_fn):
    """
    Wrap any agent function with error recovery.
    If the agent raises, returns a failed AgentResult instead of crashing the graph.
    """
    def wrapper(state: AgentState) -> dict:
        try:
            return agent_fn(state)
        except Exception as exc:
            agent_name = agent_fn.__name__ if hasattr(agent_fn, '__name__') else "unknown_agent"
            logger.error("Agent %s raised an exception: %s", agent_name, exc, exc_info=True)
            # Return a failed result — other agents and the supervisor still run
            return {
                "agent_results": {
                    agent_name: {
                        "agent_name": agent_name,
                        "status": "failed",
                        "result": {"error": str(exc)},
                        "tools_used": [],
                        "execution_time_ms": 0.0,
                        "confidence_score": 0.0,
                    }
                }
            }
    wrapper.__name__ = getattr(agent_fn, '__name__', 'agent')
    return wrapper


def route_to_agents(state: AgentState) -> list[str]:
    """
    Conditional routing: After the Planner runs, route to only the agents it selected.
    This is the key "selective spawning" logic.
    """
    agents_to_spawn = state.get("agents_to_spawn", [])

    valid_agents = {"asset_agent", "alarm_agent", "energy_agent", "documentation_agent"}
    selected = [a for a in agents_to_spawn if a in valid_agents]

    if not selected:
        logger.warning("Planner selected no valid agents — defaulting to documentation_agent")
        selected = ["documentation_agent"]

    return selected


def build_graph() -> StateGraph:
    """Build the LangGraph state machine for agent orchestration."""
    graph = StateGraph(AgentState)

    # ── Register nodes (with error recovery wrappers on specialists) ──────
    graph.add_node("planner", planner_agent)
    graph.add_node("asset_agent", _safe_agent(asset_agent))
    graph.add_node("alarm_agent", _safe_agent(alarm_agent))
    graph.add_node("energy_agent", _safe_agent(energy_agent))
    graph.add_node("documentation_agent", _safe_agent(documentation_agent))
    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("verification", verification_agent)

    # ── Entry point ────────────────────────────────────────────────────────
    graph.set_entry_point("planner")

    # ── Conditional edges: planner routes to selected specialists ─────────
    graph.add_conditional_edges(
        "planner",
        route_to_agents,
        {
            "asset_agent": "asset_agent",
            "alarm_agent": "alarm_agent",
            "energy_agent": "energy_agent",
            "documentation_agent": "documentation_agent",
        },
    )

    # ── All specialists converge on supervisor ─────────────────────────────
    graph.add_edge("asset_agent", "supervisor")
    graph.add_edge("alarm_agent", "supervisor")
    graph.add_edge("energy_agent", "supervisor")
    graph.add_edge("documentation_agent", "supervisor")

    # ── Supervisor → Verification → END ───────────────────────────────────
    graph.add_edge("supervisor", "verification")
    graph.add_edge("verification", END)

    return graph


def create_app():
    """Compile the LangGraph application with MemorySaver for session continuity."""
    graph = build_graph()
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# Singleton compiled graph
agent_graph = create_app()
