"""
Unit tests for agent-level logic.
Tests planner JSON parsing, fallback behavior, and verification agent grounding.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from agents.verification_agent import (
    _extract_claims_from_response,
    _extract_values_from_raw_data,
)


# ── Planner JSON Parsing ──────────────────────────────────────────────────────

class TestPlannerParsing:
    def test_extract_claims_finds_numbers(self):
        text = "The temperature is 82.5°F and the power draw is 125 kW"
        claims = _extract_claims_from_response(text)
        assert "82.5" in claims or "125" in claims

    def test_extract_claims_finds_asset_ids(self):
        text = "AHU-01 is reporting a fault. Chiller-01 is operating normally."
        claims = _extract_claims_from_response(text)
        assert "AHU-01" in claims
        assert "CHILLER-01" in claims

    def test_extract_claims_empty_text(self):
        claims = _extract_claims_from_response("")
        assert isinstance(claims, set)
        assert len(claims) == 0


# ── Verification Agent ────────────────────────────────────────────────────────

class TestVerificationAgent:
    def test_extract_raw_values_from_agent_results(self):
        agent_results = {
            "alarm_agent": {
                "status": "completed",
                "result": {"currentTemp": 82.5, "assetId": "AHU-01"},
            }
        }
        values = _extract_values_from_raw_data(agent_results)
        assert "82.5" in values
        assert "AHU-01" in values

    def test_grounded_claim_when_value_in_data(self):
        """A value that exists in tool data should be grounded."""
        response = "The supply air temperature is 82.5°F on AHU-01."
        agent_results = {
            "alarm_agent": {
                "status": "completed",
                "result": {"supplyAirTemp": 82.5, "assetId": "AHU-01"},
            }
        }
        response_claims = _extract_claims_from_response(response)
        raw_values = _extract_values_from_raw_data(agent_results)

        grounded = [c for c in response_claims if c in raw_values]
        assert len(grounded) > 0

    def test_ungrounded_claim_when_value_not_in_data(self):
        """A fabricated value should NOT be grounded."""
        response = "The supply air temperature is 999.9°F."
        agent_results = {
            "alarm_agent": {
                "status": "completed",
                "result": {"supplyAirTemp": 82.5},
            }
        }
        response_claims = _extract_claims_from_response(response)
        raw_values = _extract_values_from_raw_data(agent_results)

        ungrounded = [c for c in response_claims if c not in raw_values]
        assert "999.9" in ungrounded

    def test_verification_agent_runs_full_flow(self):
        """Integration test: verification_agent returns a result dict."""
        from agents.verification_agent import verification_agent

        state = {
            "final_response": "AHU-01 has a supply air temp of 82.5°F.",
            "agent_results": {
                "alarm_agent": {
                    "status": "completed",
                    "result": {"temp": 82.5, "asset": "AHU-01"},
                    "tools_used": ["get_alarm_history"],
                    "agent_name": "Alarm Agent",
                }
            },
            "reasoning_trace": [],
        }

        result = verification_agent(state)
        assert "verification_result" in result
        vr = result["verification_result"]
        assert "confidence_score" in vr
        assert "status" in vr
        assert vr["status"] in {"VERIFIED", "PARTIAL", "UNVERIFIED"}
        assert 0.0 <= vr["confidence_score"] <= 1.0

    def test_confidence_score_high_when_all_agents_complete(self):
        from agents.verification_agent import verification_agent

        state = {
            "final_response": "COP is 5.8 for Chiller-01.",
            "agent_results": {
                "energy_agent": {
                    "status": "completed",
                    "result": {"cop": 5.8, "assetId": "Chiller-01"},
                    "tools_used": ["get_energy_data"],
                    "agent_name": "Energy Agent",
                }
            },
            "reasoning_trace": [],
        }

        result = verification_agent(state)
        vr = result["verification_result"]
        assert vr["agents_completed"] == 1
        assert vr["agents_total"] == 1
        assert vr["confidence_score"] > 0.4

    def test_empty_response_does_not_crash(self):
        from agents.verification_agent import verification_agent

        state = {
            "final_response": "",
            "agent_results": {},
            "reasoning_trace": [],
        }

        result = verification_agent(state)
        assert "verification_result" in result
