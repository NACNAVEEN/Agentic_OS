"""Mock Energy Tools — Simulated energy data retrieval and analysis.

New: parameters_schema on each tool, module-level data cache.
"""
import json
import os
from typing import Any
from tools.base_tool import BaseTool, _CACHE

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "energy.json")


def _load_energy() -> dict:
    """Load energy data with module-level caching."""
    if "energy" not in _CACHE:
        with open(DATA_PATH, "r") as f:
            _CACHE["energy"] = json.load(f)
    return _CACHE["energy"]


class MockGetEnergyData(BaseTool):
    """Retrieve current energy data for an asset or building."""

    @property
    def name(self) -> str:
        return "get_energy_data"

    @property
    def description(self) -> str:
        return (
            "Retrieve current energy consumption data for a specific asset. "
            "Input: asset_id (string, e.g. 'Chiller-01', 'AHU-01')"
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "string",
                    "description": "Asset identifier, e.g. 'Chiller-01'",
                    "default": "",
                }
            },
            "required": ["asset_id"],
        }

    def _execute(self, asset_id: str = "", **kwargs) -> Any:
        energy = _load_energy()
        if asset_id in energy.get("assets", {}):
            asset_data = energy["assets"][asset_id]
            return {
                "asset": asset_id,
                "currentPower": asset_data["currentPower"],
                "powerUnit": asset_data["powerUnit"],
                "efficiency": asset_data["efficiency"],
                "todayConsumption": (
                    asset_data["dailyConsumption"][-1]
                    if asset_data["dailyConsumption"]
                    else None
                ),
                "weeklyTotal": sum(d["consumption"] for d in asset_data["dailyConsumption"]),
            }
        return {
            "error": f"No energy data for asset '{asset_id}'",
            "available": list(energy.get("assets", {}).keys()),
        }


class MockGetConsumptionTrend(BaseTool):
    """Retrieve consumption trend data over a period."""

    @property
    def name(self) -> str:
        return "get_consumption_trend"

    @property
    def description(self) -> str:
        return (
            "Retrieve energy consumption trend over a period. "
            "Input: asset_id (string), period (string: 'daily' or 'monthly')"
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "string",
                    "description": "Asset identifier",
                    "default": "",
                },
                "period": {
                    "type": "string",
                    "description": "'daily' or 'monthly'",
                    "default": "daily",
                },
            },
        }

    def _execute(self, asset_id: str = "", period: str = "daily", **kwargs) -> Any:
        energy = _load_energy()
        if period == "monthly":
            buildings = energy.get("buildings", [])
            if buildings:
                building = buildings[0]
                return {
                    "building": building["name"],
                    "area": f"{building['totalArea']} {building['areaUnit']}",
                    "trend": building["monthlyConsumption"],
                    "costRate": energy.get("costRate", {}),
                }
        if asset_id in energy.get("assets", {}):
            asset_data = energy["assets"][asset_id]
            return {
                "asset": asset_id,
                "period": period,
                "trend": asset_data["dailyConsumption"],
                "currentPower": asset_data["currentPower"],
                "powerUnit": asset_data["powerUnit"],
            }
        return {"error": f"No trend data for '{asset_id}'"}


class MockGetPeakDemand(BaseTool):
    """Retrieve peak demand and utility rate information."""

    @property
    def name(self) -> str:
        return "get_peak_demand"

    @property
    def description(self) -> str:
        return "Retrieve current peak demand data and utilization information. No input required."

    @property
    def parameters_schema(self) -> dict:
        return {"type": "object", "properties": {}}

    def _execute(self, **kwargs) -> Any:
        energy = _load_energy()
        peak = energy.get("peakDemand", {})
        cost = energy.get("costRate", {})
        buildings = energy.get("buildings", [])
        monthly_last = (
            buildings[0].get("monthlyConsumption", [{}])[-1] if buildings else None
        )
        return {
            "peakDemand": peak,
            "costRates": cost,
            "monthlyBuildingData": monthly_last,
        }
