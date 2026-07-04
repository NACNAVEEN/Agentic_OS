"""Mock Asset Tools — Simulated asset data retrieval.

New: parameters_schema on each tool, module-level data cache.
"""
import json
import os
from typing import Any
from tools.base_tool import BaseTool, _CACHE

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "assets.json")


def _load_assets() -> list[dict]:
    """Load asset data with module-level caching."""
    if "assets" not in _CACHE:
        with open(DATA_PATH, "r") as f:
            _CACHE["assets"] = json.load(f)
    return _CACHE["assets"]


class MockGetAsset(BaseTool):
    """Retrieve detailed information about a specific asset by ID."""

    @property
    def name(self) -> str:
        return "get_asset"

    @property
    def description(self) -> str:
        return (
            "Retrieve detailed asset information including type, location, status, "
            "specifications, and connected equipment. Input: asset_id (string)"
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "string",
                    "description": "Asset identifier, e.g. 'AHU-01', 'Chiller-01'",
                    "default": "",
                }
            },
            "required": ["asset_id"],
        }

    def _execute(self, asset_id: str = "", **kwargs) -> Any:
        assets = _load_assets()
        for asset in assets:
            if asset["assetId"].lower() == asset_id.lower():
                return asset
        return {
            "error": f"Asset '{asset_id}' not found",
            "available_assets": [a["assetId"] for a in assets],
        }


class MockSearchAssets(BaseTool):
    """Search assets by query string."""

    @property
    def name(self) -> str:
        return "search_assets"

    @property
    def description(self) -> str:
        return "Search for assets by name, type, or location. Returns matching assets. Input: query (string)"

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term (name, type, or location)",
                    "default": "",
                }
            },
            "required": ["query"],
        }

    def _execute(self, query: str = "", **kwargs) -> Any:
        assets = _load_assets()
        query_lower = query.lower()
        results = []
        for asset in assets:
            searchable = (
                f"{asset['assetId']} {asset['name']} {asset['type']} "
                f"{asset['location']} {asset['status']}"
            ).lower()
            if query_lower in searchable:
                results.append({
                    "assetId": asset["assetId"],
                    "name": asset["name"],
                    "type": asset["type"],
                    "location": asset["location"],
                    "status": asset["status"],
                })
        return {"query": query, "results": results, "count": len(results)}


class MockGetRelatedAssets(BaseTool):
    """Get assets connected to a specific asset."""

    @property
    def name(self) -> str:
        return "get_related_assets"

    @property
    def description(self) -> str:
        return "Get all assets connected or related to a given asset. Input: asset_id (string)"

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
            "required": ["asset_id"],
        }

    def _execute(self, asset_id: str = "", **kwargs) -> Any:
        assets = _load_assets()
        asset_map = {a["assetId"]: a for a in assets}

        target = asset_map.get(asset_id)
        if not target:
            # Try case-insensitive lookup
            for k, v in asset_map.items():
                if k.lower() == asset_id.lower():
                    target = v
                    break

        if not target:
            return {"error": f"Asset '{asset_id}' not found"}

        related = []
        for conn_id in target.get("connectedTo", []):
            if conn_id in asset_map:
                conn = asset_map[conn_id]
                related.append({
                    "assetId": conn["assetId"],
                    "name": conn["name"],
                    "type": conn["type"],
                    "status": conn["status"],
                    "relationship": "connected",
                })

        return {"asset": asset_id, "relatedAssets": related, "count": len(related)}
