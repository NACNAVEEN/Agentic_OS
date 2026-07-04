"""
Supervisor Agent — Collects all agent results, synthesizes the final response.
This is the EXIT POINT of the orchestration graph (before Verification).

Updated:
  - Uses get_llm() DI instead of inline ChatGroq
  - Adds synthesis_confidence score based on agent completion ratio
  - Instructs LLM to cite specific data values to reduce hallucination
"""
import json
import logging
import time
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from orchestrator.state import AgentState, ReasoningStep
from services.llm_factory import get_llm

logger = logging.getLogger(__name__)

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor Agent in AgenticOS, an Operations Intelligence Platform.

Your job is to synthesize results from multiple specialized agents into a clear, comprehensive response.

## Your Responsibilities:
1. Collect and review all agent outputs
2. Detect any conflicts or inconsistencies between agent findings
3. CITE SPECIFIC DATA VALUES — include exact numbers, IDs, and readings from the tool data
4. Produce a well-structured final response

## IMPORTANT — Grounding Rule:
Every numeric value or asset ID you mention MUST come directly from the agent data provided below.
Do NOT estimate or invent values. If data is missing, say "data unavailable".

## Output Structure:
Organize your response into these sections (omit any that aren't relevant):

### Executive Summary
A brief 2-3 sentence overview of the key findings with specific data values.

### Detailed Findings
The comprehensive analysis, organized by topic. Reference specific asset IDs and readings.

### Recommended Actions
Specific actionable steps based on the findings.

### Supporting Evidence
Key data points and references from the agent outputs.

Be thorough but concise. Use bullet points and clear formatting.
"""


def supervisor_agent(state: AgentState) -> dict:
    """Supervisor Agent node — synthesizes all agent results into final response."""
    start_time = time.time()

    user_query = state.get("user_query", "")
    agent_results = state.get("agent_results", {})
    execution_plan = state.get("execution_plan", {})

    new_reasoning: list[ReasoningStep] = []
    new_reasoning.append(ReasoningStep(
        agent="Supervisor Agent",
        thought=f"Collecting results from {len(agent_results)} agents",
        action="Synthesizing final response with grounded data citations",
        timestamp=datetime.now(timezone.utc).isoformat(),
    ))

    # ── Build agent context ────────────────────────────────────────────────
    agent_context_parts = []
    for agent_name, result in agent_results.items():
        if result.get("status") == "completed":
            agent_context_parts.append(
                f"### {result['agent_name']} Results\n"
                f"Tools Used: {', '.join(result.get('tools_used', []))}\n"
                f"Data:\n```json\n{json.dumps(result.get('result', {}), indent=2, default=str)}\n```"
            )

    agent_context = "\n\n".join(agent_context_parts)
    plan_context = json.dumps(execution_plan, indent=2, default=str)

    synthesis_prompt = f"""## User Query
{user_query}

## Execution Plan
{plan_context}

## Agent Results
{agent_context}

Based on the above information, provide a comprehensive response to the user's query.
IMPORTANT: Only cite values that appear explicitly in the Agent Results above.
If a value is not in the data, do not include it."""

    # ── LLM call via DI factory ────────────────────────────────────────────
    llm = get_llm(temperature=0.3, max_tokens=2048)
    response = llm.invoke([
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=synthesis_prompt),
    ])

    prompt_tokens = response.response_metadata.get("token_usage", {}).get("prompt_tokens", 0)
    completion_tokens = response.response_metadata.get("token_usage", {}).get("completion_tokens", 0)

    final_response = response.content

    # ── Compute synthesis confidence ───────────────────────────────────────
    total_agents = len(agent_results)
    completed = sum(1 for r in agent_results.values() if r.get("status") == "completed")
    synthesis_confidence = round(completed / total_agents, 2) if total_agents > 0 else 0.0

    elapsed = (time.time() - start_time) * 1000
    logger.info("Supervisor synthesis complete in %.0fms. Confidence: %.0f%%", elapsed, synthesis_confidence * 100)

    new_reasoning.append(ReasoningStep(
        agent="Supervisor Agent",
        thought=f"Synthesis complete. {completed}/{total_agents} agents contributed. Confidence: {synthesis_confidence:.0%}",
        action="Final response delivered — passing to Verification Agent.",
        timestamp=datetime.now(timezone.utc).isoformat(),
    ))

    return {
        "messages": [AIMessage(content=final_response)],
        "final_response": final_response,
        "reasoning_trace": new_reasoning,
        "total_prompt_tokens": prompt_tokens,
        "total_completion_tokens": completion_tokens,
    }
