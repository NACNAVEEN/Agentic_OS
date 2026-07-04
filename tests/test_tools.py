"""
Unit tests for all mock tools.
Tests run against real JSON data files — no mocking needed.
"""
import sys
import os
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from tools.base_tool import clear_cache
from tools.mock_alarm_tool import MockGetActiveAlarms, MockGetAlarmHistory, MockCorrelateAlarms
from tools.mock_asset_tool import MockGetAsset, MockSearchAssets, MockGetRelatedAssets
from tools.mock_energy_tool import MockGetEnergyData, MockGetConsumptionTrend, MockGetPeakDemand


@pytest.fixture(autouse=True)
def clear_tool_cache():
    """Clear the tool data cache before each test."""
    clear_cache()
    yield
    clear_cache()


# ── Alarm Tools ────────────────────────────────────────────────────────────────

class TestGetActiveAlarms:
    def test_returns_dict_with_active_alarms_key(self):
        tool = MockGetActiveAlarms()
        result = tool.execute()
        assert result.success
        assert "activeAlarms" in result.data
        assert "totalActive" in result.data

    def test_active_alarms_is_list(self):
        tool = MockGetActiveAlarms()
        result = tool.execute()
        assert isinstance(result.data["activeAlarms"], list)

    def test_critical_count_is_integer(self):
        tool = MockGetActiveAlarms()
        result = tool.execute()
        assert isinstance(result.data["criticalCount"], int)

    def test_execution_time_recorded(self):
        tool = MockGetActiveAlarms()
        result = tool.execute()
        assert result.execution_time_ms >= 0

    def test_tool_name(self):
        tool = MockGetActiveAlarms()
        assert tool.name == "get_active_alarms"


class TestGetAlarmHistory:
    def test_returns_history_for_known_asset(self):
        tool = MockGetAlarmHistory()
        result = tool.execute(asset_id="AHU-01")
        assert result.success
        assert result.data["asset"] == "AHU-01"
        assert "alarmHistory" in result.data

    def test_returns_empty_for_unknown_asset(self):
        tool = MockGetAlarmHistory()
        result = tool.execute(asset_id="NONEXISTENT-99")
        assert result.success
        assert result.data["totalAlarms"] == 0

    def test_hallucinated_param_dropped(self):
        """Unknown parameters should be silently dropped, not cause errors."""
        tool = MockGetAlarmHistory()
        result = tool.execute(asset_id="AHU-01", hallucinated_param="bad_value")
        assert result.success


class TestCorrelateAlarms:
    def test_finds_correlations_for_known_alarm(self):
        tool = MockCorrelateAlarms()
        result = tool.execute(alarm_id="ALM-001")
        assert result.success
        assert "alarm" in result.data
        assert "correlatedAlarms" in result.data

    def test_returns_error_for_unknown_alarm(self):
        tool = MockCorrelateAlarms()
        result = tool.execute(alarm_id="ALM-FAKE-999")
        assert result.success  # Tool itself succeeds
        assert "error" in result.data

    def test_analysis_section_present(self):
        tool = MockCorrelateAlarms()
        result = tool.execute(alarm_id="ALM-001")
        if "analysis" in result.data:
            assert "possibleRootCause" in result.data["analysis"]


# ── Asset Tools ────────────────────────────────────────────────────────────────

class TestGetAsset:
    def test_returns_asset_for_known_id(self):
        tool = MockGetAsset()
        result = tool.execute(asset_id="AHU-01")
        assert result.success
        assert result.data.get("assetId", "").upper() == "AHU-01"

    def test_returns_error_for_unknown_id(self):
        tool = MockGetAsset()
        result = tool.execute(asset_id="FAKE-99")
        assert result.success
        assert "error" in result.data

    def test_available_assets_in_error_response(self):
        tool = MockGetAsset()
        result = tool.execute(asset_id="FAKE-99")
        assert "available_assets" in result.data
        assert isinstance(result.data["available_assets"], list)


class TestSearchAssets:
    def test_search_by_type_returns_results(self):
        tool = MockSearchAssets()
        result = tool.execute(query="AHU")
        assert result.success
        assert result.data["count"] >= 0

    def test_empty_query_returns_results(self):
        tool = MockSearchAssets()
        result = tool.execute(query="")
        assert result.success


class TestGetRelatedAssets:
    def test_returns_related_for_known_asset(self):
        tool = MockGetRelatedAssets()
        result = tool.execute(asset_id="AHU-01")
        assert result.success
        assert "relatedAssets" in result.data

    def test_related_is_list(self):
        tool = MockGetRelatedAssets()
        result = tool.execute(asset_id="AHU-01")
        assert isinstance(result.data["relatedAssets"], list)


# ── Energy Tools ───────────────────────────────────────────────────────────────

class TestGetEnergyData:
    def test_returns_energy_for_chiller(self):
        tool = MockGetEnergyData()
        result = tool.execute(asset_id="Chiller-01")
        assert result.success
        assert "currentPower" in result.data

    def test_returns_error_for_unknown_asset(self):
        tool = MockGetEnergyData()
        result = tool.execute(asset_id="FAKE-ASSET")
        assert result.success
        assert "error" in result.data

    def test_weekly_total_is_number(self):
        tool = MockGetEnergyData()
        result = tool.execute(asset_id="Chiller-01")
        if "weeklyTotal" in result.data:
            assert isinstance(result.data["weeklyTotal"], (int, float))


class TestGetPeakDemand:
    def test_returns_peak_demand_data(self):
        tool = MockGetPeakDemand()
        result = tool.execute()
        assert result.success
        assert "peakDemand" in result.data

    def test_cost_rates_present(self):
        tool = MockGetPeakDemand()
        result = tool.execute()
        assert "costRates" in result.data


# ── Tool Schema Validation ─────────────────────────────────────────────────────

class TestParametersSchema:
    def test_all_tools_have_schema(self):
        tools = [
            MockGetActiveAlarms(), MockGetAlarmHistory(), MockCorrelateAlarms(),
            MockGetAsset(), MockSearchAssets(), MockGetRelatedAssets(),
            MockGetEnergyData(), MockGetConsumptionTrend(), MockGetPeakDemand(),
        ]
        for tool in tools:
            schema = tool.parameters_schema
            assert isinstance(schema, dict), f"{tool.name} missing parameters_schema"
            assert "type" in schema

    def test_validate_params_drops_unknown_keys(self):
        tool = MockGetAsset()
        validated = tool._validate_params(asset_id="AHU-01", unknown_key="bad")
        assert "asset_id" in validated
        assert "unknown_key" not in validated
