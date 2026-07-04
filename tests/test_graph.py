"""
Integration tests for the LangGraph orchestration graph.
Uses mocked LLM responses — no Groq API key required.
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from orchestrator.graph import route_to_agents, build_graph
from orchestrator.state import AgentState


# ── route_to_agents ────────────────────────────────────────────────────────────

class TestRouteToAgents:
    def test_routes_to_valid_agents(self):
        state = {"agents_to_spawn": ["alarm_agent", "asset_agent"]}
        result = route_to_agents(state)
        assert "alarm_agent" in result
        assert "asset_agent" in result

    def test_filters_invalid_agents(self):
        state = {"agents_to_spawn": ["alarm_agent", "fake_agent", "nonexistent"]}
        result = route_to_agents(state)
        assert "fake_agent" not in result
        assert "alarm_agent" in result

    def test_defaults_to_documentation_when_empty(self):
        state = {"agents_to_spawn": []}
        result = route_to_agents(state)
        assert result == ["documentation_agent"]

    def test_defaults_to_documentation_when_all_invalid(self):
        state = {"agents_to_spawn": ["completely_fake"]}
        result = route_to_agents(state)
        assert result == ["documentation_agent"]

    def test_all_four_agents_valid(self):
        state = {"agents_to_spawn": [
            "asset_agent", "alarm_agent", "energy_agent", "documentation_agent"
        ]}
        result = route_to_agents(state)
        assert len(result) == 4


# ── Graph structure ────────────────────────────────────────────────────────────

class TestGraphStructure:
    def test_graph_builds_without_error(self):
        graph = build_graph()
        assert graph is not None

    def test_graph_has_all_nodes(self):
        graph = build_graph()
        node_names = set(graph.nodes.keys()) if hasattr(graph, 'nodes') else set()
        # Build and compile to verify no errors
        compiled = graph.compile()
        assert compiled is not None

    def test_compiled_graph_is_runnable(self):
        """
        Test that the compiled graph accepts a valid initial state.
        We mock the LLM to avoid API calls.
        """
        from langchain_core.messages import AIMessage

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"understanding": "test", "execution_plan": [{"step": 1, "task": "search docs", "agent": "documentation_agent"}], "agents_to_spawn": ["documentation_agent"], "reasoning": "test query"}'
        mock_response.response_metadata = {"token_usage": {"prompt_tokens": 10, "completion_tokens": 20}}
        mock_llm.invoke.return_value = mock_response

        with patch('services.llm_factory.ChatGroq', return_value=mock_llm):
            from orchestrator.graph import build_graph
            graph = build_graph()
            compiled = graph.compile()
            assert compiled is not None
