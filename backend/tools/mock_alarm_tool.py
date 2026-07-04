"""Mock Alarm Tools — Simulated alarm data retrieval and analysis.

New: parameters_schema on each tool, module-level data cache.
"""
import json
import os
from typing import Any
from tools.base_tool import BaseTool, _CACHE

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "alarms.json")


def _load_alarms() -> list[dict]:
    """Load alarm data with module-level caching."""
    if "alarms" not in _CACHE:
        with open(DATA_PATH, "r") as f:
            _CACHE["alarms"] = json.load(f)
    return _CACHE["alarms"]


class MockGetActiveAlarms(BaseTool):
    """Retrieve all currently active alarms."""

    @property
    def name(self) -> str:
        return "get_active_alarms"

    @property
    def description(self) -> str:
        return (
            "Retrieve all currently active alarms across all assets. "
            "Returns alarm details including severity, asset, and timestamp. "
            "No input required."
        )

    @property
    def parameters_schema(self) -> dict:
        return {"type": "object", "properties": {}}

    def _execute(self, **kwargs) -> Any:
        alarms = _load_alarms()
        active = [a for a in alarms if not a.get("acknowledged", False)]
        return {
            "activeAlarms": active,
            "totalActive": len(active),
            "criticalCount": len([a for a in active if a["severity"] == "Critical"]),
            "warningCount": len([a for a in active if a["severity"] == "Warning"]),
        }


class MockGetAlarmHistory(BaseTool):
    """Retrieve alarm history for a specific asset."""

    @property
    def name(self) -> str:
        return "get_alarm_history"

    @property
    def description(self) -> str:
        return "Retrieve alarm history for a specific asset. Input: asset_id (string, e.g. 'AHU-01')"

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "string",
                    "description": "Asset identifier, e.g. 'AHU-01'",
                    "default": "",
                }
            },
        }

    def _execute(self, asset_id: str = "", **kwargs) -> Any:
        alarms = _load_alarms()
        asset_alarms = [a for a in alarms if a["asset"].lower() == asset_id.lower()]
        return {
            "asset": asset_id,
            "alarmHistory": asset_alarms,
            "totalAlarms": len(asset_alarms),
            "criticalCount": len([a for a in asset_alarms if a["severity"] == "Critical"]),
            "warningCount": len([a for a in asset_alarms if a["severity"] == "Warning"]),
        }


class MockCorrelateAlarms(BaseTool):
    """Correlate alarms to find related issues and root causes."""

    @property
    def name(self) -> str:
        return "correlate_alarms"

    @property
    def description(self) -> str:
        return (
            "Analyze alarm correlations to identify related alarms and potential root causes. "
            "Input: alarm_id (string, e.g. 'ALM-001')"
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "alarm_id": {
                    "type": "string",
                    "description": "Alarm identifier, e.g. 'ALM-001'",
                    "default": "",
                }
            },
        }

    def _execute(self, alarm_id: str = "", **kwargs) -> Any:
        alarms = _load_alarms()
        target = next((a for a in alarms if a["alarmId"].lower() == alarm_id.lower()), None)

        if not target:
            return {"error": f"Alarm '{alarm_id}' not found", "available": [a["alarmId"] for a in alarms]}

        correlated = [
            a for a in alarms
            if a["alarmId"] != alarm_id and (
                a["asset"] == target["asset"] or a["location"] == target["location"]
            )
        ]

        return {
            "alarm": target,
            "correlatedAlarms": correlated,
            "correlationCount": len(correlated),
            "analysis": {
                "possibleRootCause": target.get("possibleCauses", ["Unknown"])[0],
                "recommendedActions": target.get("recommendedActions", []),
                "impactedAssets": list(set([target["asset"]] + [a["asset"] for a in correlated])),
            },
        }
