"""
Verification Agent — Deterministic hallucination prevention layer.

Runs AFTER the Supervisor. No extra LLM call needed.
Cross-references every numeric claim and asset ID in the final response
against the raw tool data returned by specialized agents.

Produces:
  - confidence_score (0.0 – 1.0)
  - grounded_claims  (found in raw data)
  - ungrounded_claims (NOT found — potential hallucinations)
  - verification_status: VERIFIED | PARTIAL | UNVERIFIED
"""
import re
import json
import logging
from datetime import datetime, timezone
from orchestrator.state import AgentState, ReasoningStep

logger = logging.getLogger(__name__)

# Patterns for claims we can verify
_NUMBER_PATTERN = re.compile(r'\b(\d+(?:\.\d+)?)\s*(?:kW|kWh|°F|°C|%|psi|tons|cfm)?\b')
_ASSET_ID_PATTERN = re.compile(r'\b((?:AHU|Chiller|VAV|FCU|RTU|PUMP|CW|ALM)-\d+)\b', re.IGNORECASE)


def _extract_claims_from_response(text: str) -> set[str]:
    """Pull numeric values and asset IDs from the Supervisor's text response."""
    claims: set[str] = set()
    for m in _NUMBER_PATTERN.finditer(text):
        claims.add(m.group(1))          # just the number, e.g. "82.5"
    for m in _ASSET_ID_PATTERN.finditer(text):
        claims.add(m.group(1).upper())  # normalised ID, e.g. "AHU-01"
    return claims


def _extract_values_from_raw_data(agent_results: dict) -> set[str]:
    """Flatten all agent result data into a set of raw strings for lookup."""
    raw_json = json.dumps(agent_results, default=str)
    raw_values: set[str] = set()
    for m in _NUMBER_PATTERN.finditer(raw_json):
        raw_values.add(m.group(1))
    for m in _ASSET_ID_PATTERN.finditer(raw_json):
        raw_values.add(m.group(1).upper())
    return raw_values


def verification_agent(state: AgentState) -> dict:
    """
    Verification Agent node — post-Supervisor grounding check.
    Returns ONLY new state keys (verification_result + reasoning_trace delta).
    """
    final_response = state.get("final_response", "")
    agent_results = state.get("agent_results", {})

    new_reasoning: list[ReasoningStep] = [ReasoningStep(
        agent="Verification Agent",
        thought="Cross-referencing final response claims against raw tool data.",
        action="Running deterministic grounding and confidence analysis.",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )]

    # ── 1. Extract claims from the Supervisor's response ──────────────────
    response_claims = _extract_claims_from_response(final_response)

    # ── 2. Extract all verifiable values from raw tool data ───────────────
    raw_values = _extract_values_from_raw_data(agent_results)

    # ── 3. Classify each claim ────────────────────────────────────────────
    grounded: list[str] = []
    ungrounded: list[str] = []

    for claim in response_claims:
        if claim in raw_values:
            grounded.append(claim)
        else:
            ungrounded.append(claim)

    # ── 4. Compute confidence score ───────────────────────────────────────
    total_agents = len(agent_results)
    completed = sum(1 for r in agent_results.values() if r.get("status") == "completed")
    agent_ratio = completed / total_agents if total_agents > 0 else 1.0
    claim_ratio = len(grounded) / len(response_claims) if response_claims else 1.0

    # Weighted: 40% agent completion, 60% claim grounding
    confidence_score = round(agent_ratio * 0.4 + claim_ratio * 0.6, 2)

    if confidence_score >= 0.80:
        status = "VERIFIED"
    elif confidence_score >= 0.50:
        status = "PARTIAL"
    else:
        status = "UNVERIFIED"

    verification_result = {
        "status": status,
        "confidence_score": confidence_score,
        "grounded_claims": sorted(grounded),
        "ungrounded_claims": sorted(ungrounded),
        "agents_completed": completed,
        "agents_total": total_agents,
        "claim_coverage": f"{len(response_claims)} claims checked",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Verification complete — status=%s confidence=%.0f%% "
        "grounded=%d ungrounded=%d",
        status, confidence_score * 100, len(grounded), len(ungrounded),
    )

    new_reasoning.append(ReasoningStep(
        agent="Verification Agent",
        thought=(
            f"Verification complete. Status: {status}. "
            f"Confidence: {confidence_score:.0%}. "
            f"{len(grounded)} claims grounded, {len(ungrounded)} ungrounded."
        ),
        action="Verification result attached to final response.",
        timestamp=datetime.now(timezone.utc).isoformat(),
    ))

    return {
        "verification_result": verification_result,
        "reasoning_trace": new_reasoning,
    }
