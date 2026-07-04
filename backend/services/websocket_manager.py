"""
WebSocket Manager — Handles AgenticOS real-time event streaming.

Extracted from main.py to separate concerns.
Manages the LangGraph astream loop and translates graph events into
typed WebSocket messages sent to the React frontend.
"""
import json
import logging
import time
from datetime import datetime, timezone

from fastapi import WebSocket
from orchestrator.state import AgentState
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class AgentWebSocketManager:
    """
    Manages the lifecycle of a single WebSocket session:
    receive query → stream graph events → send final response.
    """

    def __init__(self, agent_graph, settings):
        self.agent_graph = agent_graph
        self.settings = settings

    async def handle_query(self, websocket: WebSocket, user_query: str, session_id: str) -> None:
        """Run the agent graph for one query and stream all events to the client."""
        start_time = time.time()

        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_query)],
            "session_id": session_id,
            "user_query": user_query,
            "execution_plan": {},
            "agents_to_spawn": [],
            "agent_results": {},
            "reasoning_trace": [],
            "tool_invocations": [],
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tool_calls": 0,
            "final_response": "",
            "verification_result": {},
        }

        # Thread config for MemorySaver (enables conversation continuity)
        config = {"configurable": {"thread_id": session_id}}

        prev_reasoning_count = 0
        prev_tool_count = 0
        prev_agent_results_keys: set = set()
        planner_sent = False
        verification_sent = False

        async for event in self.agent_graph.astream(initial_state, config=config, stream_mode="values"):

            # ── Planner complete ───────────────────────────────────────────
            if event.get("execution_plan") and not planner_sent:
                plan = event["execution_plan"]
                if plan:
                    await self._send(websocket, "planner_complete", {
                        "plan": plan,
                        "agents_to_spawn": event.get("agents_to_spawn", []),
                    })
                    for agent_name in event.get("agents_to_spawn", []):
                        await self._send(websocket, "agent_spawned", {
                            "agent": agent_name,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    planner_sent = True

            # ── New reasoning steps ────────────────────────────────────────
            reasoning = event.get("reasoning_trace", [])
            if len(reasoning) > prev_reasoning_count:
                for step in reasoning[prev_reasoning_count:]:
                    await self._send(websocket, "reasoning_step", step)
                prev_reasoning_count = len(reasoning)

            # ── New tool invocations ───────────────────────────────────────
            tools = event.get("tool_invocations", [])
            if len(tools) > prev_tool_count:
                for inv in tools[prev_tool_count:]:
                    await self._send(websocket, "tool_invocation", inv)
                prev_tool_count = len(tools)

            # ── Agent completion events ────────────────────────────────────
            current_keys = set(event.get("agent_results", {}).keys())
            for agent_name in current_keys - prev_agent_results_keys:
                result = event["agent_results"][agent_name]
                await self._send(websocket, "agent_complete", {
                    "agent": agent_name,
                    "status": result.get("status", "completed"),
                    "tools_used": result.get("tools_used", []),
                    "execution_time_ms": result.get("execution_time_ms", 0),
                    "confidence_score": result.get("confidence_score", 1.0),
                })
            prev_agent_results_keys = current_keys

            # ── Verification result ────────────────────────────────────────
            verification = event.get("verification_result", {})
            if verification and not verification_sent:
                await self._send(websocket, "verification_complete", verification)
                verification_sent = True

            # ── Final response ─────────────────────────────────────────────
            if event.get("final_response"):
                total_time = (time.time() - start_time) * 1000
                await self._send(websocket, "final_response", {
                    "response": event["final_response"],
                    "execution_plan": event.get("execution_plan", {}),
                    "agent_results": {
                        k: {
                            "agent_name": v.get("agent_name", k),
                            "status": v.get("status", "unknown"),
                            "tools_used": v.get("tools_used", []),
                            "execution_time_ms": v.get("execution_time_ms", 0),
                            "confidence_score": v.get("confidence_score", 1.0),
                        }
                        for k, v in event.get("agent_results", {}).items()
                    },
                    "token_usage": {
                        "prompt_tokens": event.get("total_prompt_tokens", 0),
                        "completion_tokens": event.get("total_completion_tokens", 0),
                        "total_tokens": (
                            event.get("total_prompt_tokens", 0)
                            + event.get("total_completion_tokens", 0)
                        ),
                        "tool_calls": event.get("total_tool_calls", 0),
                    },
                    "verification_result": event.get("verification_result", {}),
                    "total_execution_time_ms": round(total_time, 2),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    @staticmethod
    async def _send(websocket: WebSocket, event_type: str, data) -> None:
        """Send a typed JSON event to the frontend."""
        await websocket.send_json({"type": event_type, "data": data})
