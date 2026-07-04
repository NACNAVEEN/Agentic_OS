"""Tool Registry — Central registry for all available tools"""
from tools.mock_asset_tool import MockGetAsset, MockSearchAssets, MockGetRelatedAssets
from tools.mock_alarm_tool import MockGetActiveAlarms, MockGetAlarmHistory, MockCorrelateAlarms
from tools.mock_energy_tool import MockGetEnergyData, MockGetConsumptionTrend, MockGetPeakDemand
from tools.mock_document_tool import MockSearchDocuments, MockRetrieveSOP


# Tool instances — swap mock → real by changing these instantiations
TOOL_REGISTRY = {
    # Asset Tools
    "get_asset": MockGetAsset(),
    "search_assets": MockSearchAssets(),
    "get_related_assets": MockGetRelatedAssets(),
    
    # Alarm Tools
    "get_active_alarms": MockGetActiveAlarms(),
    "get_alarm_history": MockGetAlarmHistory(),
    "correlate_alarms": MockCorrelateAlarms(),
    
    # Energy Tools
    "get_energy_data": MockGetEnergyData(),
    "get_consumption_trend": MockGetConsumptionTrend(),
    "get_peak_demand": MockGetPeakDemand(),
    
    # Document Tools
    "search_documents": MockSearchDocuments(),
    "retrieve_sop": MockRetrieveSOP(),
}


# Agent-specific tool mappings
AGENT_TOOLS = {
    "asset_agent": ["get_asset", "search_assets", "get_related_assets"],
    "alarm_agent": ["get_active_alarms", "get_alarm_history", "correlate_alarms"],
    "energy_agent": ["get_energy_data", "get_consumption_trend", "get_peak_demand"],
    "documentation_agent": ["search_documents", "retrieve_sop"],
}


def get_tools_for_agent(agent_name: str) -> dict:
    """Get the tools available for a specific agent"""
    tool_names = AGENT_TOOLS.get(agent_name, [])
    return {name: TOOL_REGISTRY[name] for name in tool_names if name in TOOL_REGISTRY}


def get_tool(tool_name: str):
    """Get a specific tool by name"""
    return TOOL_REGISTRY.get(tool_name)
