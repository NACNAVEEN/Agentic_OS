"""
⚠️  DEMO SCAFFOLD — Simulation Engine for AgenticOS

This module runs ONLY when GROQ_API_KEY is not configured in .env.
It provides a high-fidelity demonstration of the multi-agent orchestration flow
with realistic timing, tool calls, and pre-authored responses.

IMPORTANT: This is NOT real agent execution. The responses are pre-written and
the orchestration is simulated with asyncio delays. To run real LLM-powered agents,
set GROQ_API_KEY in your .env file.

Token counts in this mode are always 0 — real metrics require a live API key.
"""
import asyncio
import time
from datetime import datetime, timezone

# We can import mock tools to get real data for the simulation!
from tools.mock_asset_tool import MockGetAsset, MockGetRelatedAssets
from tools.mock_alarm_tool import MockGetAlarmHistory, MockCorrelateAlarms
from tools.mock_energy_tool import MockGetEnergyData
from tools.mock_document_tool import MockRetrieveSOP


async def run_agentic_simulation(websocket, user_query: str):
    """Simulates the entire LangGraph orchestration flow with WebSocket events"""
    
    query_lower = user_query.lower()
    start_time = time.time()
    
    # 1. Determine scenario and which agents to spawn
    if "bacnet" in query_lower:
        scenario = "docs"
        agents_to_spawn = ["documentation_agent"]
        plan = {
            "understanding": "Retrieve information about the BACnet protocol standard.",
            "execution_plan": [
                {"step": 1, "task": "Search technical manuals and guides for BACnet details", "agent": "documentation_agent"}
            ],
            "agents_to_spawn": agents_to_spawn,
            "reasoning": "Simple protocol explanation request. Spawned only Documentation Agent."
        }
    elif "energy" in query_lower or "consumption" in query_lower or "chiller-01" in query_lower and "temp" not in query_lower and "alarm" not in query_lower:
        scenario = "energy"
        agents_to_spawn = ["energy_agent"]
        plan = {
            "understanding": "Analyze energy performance and consumption metrics for Chiller-01.",
            "execution_plan": [
                {"step": 1, "task": "Get energy consumption and COP data for Chiller-01", "agent": "energy_agent"},
                {"step": 2, "task": "Retrieve building peak demand limits and utility rates", "agent": "energy_agent"}
            ],
            "agents_to_spawn": agents_to_spawn,
            "reasoning": "Energy usage analysis request. Spawned only Energy Agent."
        }
    elif "alarm" in query_lower or "temp" in query_lower or "investigate" in query_lower or "ahu-01" in query_lower:
        scenario = "alarm"
        agents_to_spawn = ["asset_agent", "alarm_agent", "documentation_agent"]
        plan = {
            "understanding": "Investigate the high supply air temperature alarm on AHU-01.",
            "execution_plan": [
                {"step": 1, "task": "Lookup AHU-01 asset information and downstream connections", "agent": "asset_agent"},
                {"step": 2, "task": "Analyze active alarms and correlate root cause", "agent": "alarm_agent"},
                {"step": 3, "task": "Retrieve high supply air temperature troubleshooting SOP", "agent": "documentation_agent"}
            ],
            "agents_to_spawn": agents_to_spawn,
            "reasoning": "Requires looking up equipment data, diagnosing alarm history, and cross-referencing standard procedures. Spawned Asset, Alarm, and Documentation agents."
        }
    else:
        # Full Diagnostics default
        scenario = "full"
        agents_to_spawn = ["asset_agent", "alarm_agent", "energy_agent", "documentation_agent"]
        plan = {
            "understanding": "Perform a comprehensive operational health check and diagnostics on the HVAC system.",
            "execution_plan": [
                {"step": 1, "task": "Scan assets to establish operational status and connections", "agent": "asset_agent"},
                {"step": 2, "task": "Scan active alarms across all devices", "agent": "alarm_agent"},
                {"step": 3, "task": "Check energy efficiency and peak demand limits", "agent": "energy_agent"},
                {"step": 4, "task": "Search technical guidelines and troubleshooting standard SOPs", "agent": "documentation_agent"}
            ],
            "agents_to_spawn": agents_to_spawn,
            "reasoning": "Comprehensive diagnostics requested. Spawning all specialized agents to analyze operations, alarms, energy, and documentation."
        }

    # -- STAGE 1: PLANNER RUNNING --
    await asyncio.sleep(1.0)
    await websocket.send_json({
        "type": "planner_complete",
        "data": {
            "plan": plan,
            "agents_to_spawn": agents_to_spawn,
        }
    })
    
    await websocket.send_json({
        "type": "reasoning_step",
        "data": {
            "agent": "Planner Agent",
            "thought": plan["reasoning"],
            "action": f"Spawning agents: {', '.join(agents_to_spawn)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    })

    # Mark spawned agents in graph
    for agent in agents_to_spawn:
        await websocket.send_json({
            "type": "agent_spawned",
            "data": {
                "agent": agent,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
    
    await asyncio.sleep(1.0)

    # -- STAGE 2: PARALLEL AGENT EXECUTION --
    agent_results = {}
    total_tool_calls = 0

    if "asset_agent" in agents_to_spawn:
        # Asset Agent
        t_start = time.time()
        await websocket.send_json({
            "type": "reasoning_step",
            "data": {
                "agent": "Asset Agent",
                "thought": "Looking up configuration, specifications, and related components for AHU-01/Chiller-01.",
                "action": "Calling get_asset tool.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        asset_id = "AHU-01" if "ahu" in query_lower or scenario == "alarm" or scenario == "full" else "Chiller-01"
        asset_data = MockGetAsset()._execute(asset_id=asset_id)
        total_tool_calls += 1
        
        await websocket.send_json({
            "type": "tool_invocation",
            "data": {
                "agent": "Asset Agent",
                "tool_name": "get_asset",
                "parameters": {"asset_id": asset_id},
                "output": asset_data,
                "execution_time_ms": 42.0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        await asyncio.sleep(0.8)
        
        # Related assets
        related_data = MockGetRelatedAssets()._execute(asset_id=asset_id)
        total_tool_calls += 1
        await websocket.send_json({
            "type": "tool_invocation",
            "data": {
                "agent": "Asset Agent",
                "tool_name": "get_related_assets",
                "parameters": {"asset_id": asset_id},
                "output": related_data,
                "execution_time_ms": 35.0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        agent_results["asset_agent"] = {
            "status": "completed",
            "tools_used": ["get_asset", "get_related_assets"],
            "execution_time_ms": (time.time() - t_start) * 1000,
            "result": {"asset": asset_data, "related": related_data}
        }
        
        await websocket.send_json({
            "type": "agent_complete",
            "data": {
                "agent": "asset_agent",
                "status": "completed",
                "tools_used": ["get_asset", "get_related_assets"],
                "execution_time_ms": agent_results["asset_agent"]["execution_time_ms"]
            }
        })

    if "alarm_agent" in agents_to_spawn:
        # Alarm Agent
        t_start = time.time()
        await websocket.send_json({
            "type": "reasoning_step",
            "data": {
                "agent": "Alarm Agent",
                "thought": "Retrieving active alarms and alarm history. Correlating faults to discover root causes.",
                "action": "Calling get_alarm_history and correlate_alarms tools.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        asset_id = "AHU-01" if "ahu" in query_lower or scenario == "alarm" or scenario == "full" else "Chiller-01"
        alarm_history = MockGetAlarmHistory()._execute(asset_id=asset_id)
        total_tool_calls += 1
        
        await websocket.send_json({
            "type": "tool_invocation",
            "data": {
                "agent": "Alarm Agent",
                "tool_name": "get_alarm_history",
                "parameters": {"asset_id": asset_id},
                "output": alarm_history,
                "execution_time_ms": 50.0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        await asyncio.sleep(0.9)
        
        # Correlate
        alarm_id = "ALM-001" if asset_id == "AHU-01" else "ALM-003"
        correlations = MockCorrelateAlarms()._execute(alarm_id=alarm_id)
        total_tool_calls += 1
        
        await websocket.send_json({
            "type": "tool_invocation",
            "data": {
                "agent": "Alarm Agent",
                "tool_name": "correlate_alarms",
                "parameters": {"alarm_id": alarm_id},
                "output": correlations,
                "execution_time_ms": 65.0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        agent_results["alarm_agent"] = {
            "status": "completed",
            "tools_used": ["get_alarm_history", "correlate_alarms"],
            "execution_time_ms": (time.time() - t_start) * 1000,
            "result": {"history": alarm_history, "correlation": correlations}
        }
        
        await websocket.send_json({
            "type": "agent_complete",
            "data": {
                "agent": "alarm_agent",
                "status": "completed",
                "tools_used": ["get_alarm_history", "correlate_alarms"],
                "execution_time_ms": agent_results["alarm_agent"]["execution_time_ms"]
            }
        })

    if "energy_agent" in agents_to_spawn:
        # Energy Agent
        t_start = time.time()
        await websocket.send_json({
            "type": "reasoning_step",
            "data": {
                "agent": "Energy Agent",
                "thought": "Extracting energy data, daily runtime performance, and rated coefficient of performance (COP) limits.",
                "action": "Calling get_energy_data tool.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        asset_id = "Chiller-01" if "chiller" in query_lower or scenario == "energy" else "AHU-01"
        energy_data = MockGetEnergyData()._execute(asset_id=asset_id)
        total_tool_calls += 1
        
        await websocket.send_json({
            "type": "tool_invocation",
            "data": {
                "agent": "Energy Agent",
                "tool_name": "get_energy_data",
                "parameters": {"asset_id": asset_id},
                "output": energy_data,
                "execution_time_ms": 48.0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        agent_results["energy_agent"] = {
            "status": "completed",
            "tools_used": ["get_energy_data"],
            "execution_time_ms": (time.time() - t_start) * 1000,
            "result": {"energy": energy_data}
        }
        
        await asyncio.sleep(1.0)
        
        await websocket.send_json({
            "type": "agent_complete",
            "data": {
                "agent": "energy_agent",
                "status": "completed",
                "tools_used": ["get_energy_data"],
                "execution_time_ms": agent_results["energy_agent"]["execution_time_ms"]
            }
        })

    if "documentation_agent" in agents_to_spawn:
        # Documentation Agent
        t_start = time.time()
        await websocket.send_json({
            "type": "reasoning_step",
            "data": {
                "agent": "Documentation Agent",
                "thought": "Retrieving Standard Operating Procedures (SOPs) or manuals related to query topics.",
                "action": "Calling retrieve_sop tool.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        topic = "high temperature" if "temp" in query_lower or "alarm" in query_lower else "BACnet"
        sop_data = MockRetrieveSOP()._execute(topic=topic)
        total_tool_calls += 1
        
        await websocket.send_json({
            "type": "tool_invocation",
            "data": {
                "agent": "Documentation Agent",
                "tool_name": "retrieve_sop",
                "parameters": {"topic": topic},
                "output": sop_data,
                "execution_time_ms": 55.0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        agent_results["documentation_agent"] = {
            "status": "completed",
            "tools_used": ["retrieve_sop"],
            "execution_time_ms": (time.time() - t_start) * 1000,
            "result": {"sop": sop_data}
        }
        
        await asyncio.sleep(0.7)
        
        await websocket.send_json({
            "type": "agent_complete",
            "data": {
                "agent": "documentation_agent",
                "status": "completed",
                "tools_used": ["retrieve_sop"],
                "execution_time_ms": agent_results["documentation_agent"]["execution_time_ms"]
            }
        })

    # -- STAGE 3: SUPERVISOR SYNTHESIS --
    await websocket.send_json({
        "type": "reasoning_step",
        "data": {
            "agent": "Supervisor Agent",
            "thought": "Reviewing inputs and reports from all active agents. Compiling response formatting.",
            "action": "Synthesizing executive summary, diagnostic breakdown, and recommended actions.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    })
    
    await asyncio.sleep(1.5)

    # 3. Build response based on scenario
    if scenario == "docs":
        response = """### Executive Summary
BACnet (Building Automation and Control Networks) is the industry-standard data communication protocol for building automation and control systems, standardized as ISO 16484-5.

### Detailed Findings
- **Object Types**: Standardized representations of hardware and software components, including Analog Inputs (sensors), Analog Outputs (valves/dampers), and Binary Values (state variables).
- **Network Standards**: Operates over BACnet/IP (ethernet-based) or BACnet MS/TP (RS-485 serial-based).
- **Core Services**: Includes Who-Is/I-Am for self-discovery and Read/Write Property for basic parameter access.

### Recommended Actions
1. Deploy BACnet routers if bridging MS/TP segments to a BACnet/IP backbone.
2. Ensure proper device ID segmentation to avoid collisions across the network.
3. Configure change-of-value (COV) subscriptions to reduce polling traffic on the network.
"""
    elif scenario == "energy":
        response = """### Executive Summary
Chiller-01 is operating with an efficiency rating of **COP 5.8** (against rated COP of 6.2), showing a degradation of approximately **6.5%**. Its current power draw is **125 kW**.

### Detailed Findings
- **Weekly Consumption**: Sum of daily consumption for the past 7 days is **21,550 kWh**.
- **Average Load**: Operations show constant high load (avg 83% capacity), running for 20.8 hours daily.
- **Cost Analysis**: Building A is currently utilizing **84%** of its peak demand capacity (420 kW of 500 kW limit), with demand charge rate at **$12.50 / kW**.

### Recommended Actions
1. Schedule a condenser tube inspection and cleaning, as the degradation is likely caused by minor tube fouling.
2. Shift a portion of the chiller pre-cooling cycle to off-peak hours (costing $0.08/kWh compared to $0.15/kWh on-peak).
3. Test cooling tower fan efficiency to optimize chiller condenser water approach temperature.
"""
    elif scenario == "alarm":
        response = """### Executive Summary
The critical **High Supply Air Temperature** alarm (**ALM-001**) on **AHU-01** was triggered because the supply air temperature reached **82.5°F** (target setpoint: 55.0°F). The root cause has been correlated to chilled water supply valve stuck closed or a loss of chilled water flow.

### Detailed Findings
- **Equipment Profile**: AHU-01 is a Carrier unit servicing Floor 2 (Zone 2A). Its status is Running but it is failing to deliver cooled air.
- **Correlations**:
  - Connected device **VAV-03** is reporting a stuck damper fault.
  - Room 201 (serviced by VAV-01) is reporting a High Zone Temperature alarm of **78.2°F**.
  - **Chiller-01** (which feeds cold water to AHU-01) is running normally at COP 5.8, suggesting the issue is localized to the AHU valve or coil loop.
- **Reference SOP**: SOP-001 indicates checking the chilled water valve position first, then verifying chilled water coil differential pressure.

### Recommended Actions
1. **Inspect Valve Actuator**: Manually verify if the AHU-01 chilled water valve actuator is responding to 0-10V control signal, or if it is mechanically stuck closed.
2. **Check Coil Flow**: Bleed air from the AHU-01 chilled water coil to eliminate airlocks that block heat exchange.
3. **Inspect VAV-03 Actuator**: Schedule a technician to cycle the VAV-03 damper actuator, which was correlated to this failure event.
"""
    else:
        # Full diagnostics
        response = """### Executive Summary
An end-to-end operational diagnostic check of Building A reveals stable performance with a single critical alarm on **AHU-01** (Supply air temp at 82.5°F vs 55°F target) and a secondary stuck damper alert on **VAV-03**.

### Detailed Findings
- **Assets Status**: 10 primary HVAC assets scanned. 8 Running, 1 Standby, 1 Fault state (VAV-03).
- **Alarm Correlation**: The High Supply Temp alarm on AHU-01 is causing high zone temperatures in Room 201 (78.2°F) and Room 210.
- **Energy Metric**: Chiller-01 is pulling **125 kW** with 6.5% efficiency degradation. Total building peak demand remains safe at 420 kW.

### Recommended Actions
1. Resolve AHU-01 high temperature issue by checking chilled water valve actuator.
2. Repair stuck damper on VAV-03.
3. Schedule periodic tube cleaning for Chiller-01 to recover 6.5% efficiency loss.
"""

    total_time = (time.time() - start_time) * 1000
    
    # 4. Send final response
    await websocket.send_json({
        "type": "final_response",
        "data": {
            "response": response,
            "execution_plan": plan,
            "agent_results": {
                k: {
                    "agent_name": AGENT_DISPLAY_NAMES_MAPPING.get(k, k),
                    "status": v["status"],
                    "tools_used": v["tools_used"],
                    "execution_time_ms": v["execution_time_ms"]
                }
                for k, v in agent_results.items()
            },
            "token_usage": {
                # DEMO MODE: Real token counts unavailable without a Groq API key.
                # Configure GROQ_API_KEY in .env to see actual measured values.
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "tool_calls": total_tool_calls
            },
            "total_execution_time_ms": round(total_time, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    })

AGENT_DISPLAY_NAMES_MAPPING = {
  "planner": "Planner Agent",
  "asset_agent": "Asset Agent",
  "alarm_agent": "Alarm Agent",
  "energy_agent": "Energy Agent",
  "documentation_agent": "Documentation Agent",
  "supervisor": "Supervisor Agent",
}
