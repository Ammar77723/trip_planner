"""
MCP Tools wrapper for CrewAI agents.
These tools allow agents to interact with the MCP server.
MCP Server is still the core - we just wrap the functions as LangChain Tools.
"""
import requests
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")


class MCPTool:
    """Base class for MCP tools - still uses MCP server"""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.base_url = f"{MCP_SERVER_URL}/mcp/tools/{tool_name}"
    
    def call(self, **kwargs) -> Dict[str, Any]:
        """Call the MCP tool endpoint"""
        try:
            response = requests.post(
                self.base_url,
                json=kwargs,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}


@tool
def list_region_snapshot(region: str) -> str:
    """
    Get the latest flight snapshot for a region.
    
    Args:
        region: Region identifier (e.g., 'data', 'region1')
    
    Returns:
        JSON string with flight data
    """
    tool = MCPTool("flights.list_region_snapshot")
    result = tool.call(region=region)
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    data = result.get("result", {})
    flights = data.get("flights", [])
    count = len(flights) if isinstance(flights, list) else 0
    
    return f"Region '{region}' snapshot: {count} flights found. Data: {str(data)[:500]}..."


@tool
def get_flight_by_callsign(callsign: str, region: Optional[str] = None) -> str:
    """
    Find a flight by its callsign.
    
    Args:
        callsign: Flight callsign (e.g., 'SWR7YT')
        region: Optional region identifier
    
    Returns:
        JSON string with flight information
    """
    tool = MCPTool("flights.get_by_callsign")
    params = {"callsign": callsign}
    if region:
        params["region"] = region
    
    result = tool.call(**params)
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    flight = result.get("result", {})
    if flight:
        return f"Flight {callsign} found: Altitude={flight.get('baro_altitude')}m, Speed={flight.get('velocity')}m/s, Position=({flight.get('latitude')}, {flight.get('longitude')})"
    else:
        return f"Flight {callsign} not found"


@tool
def list_active_alerts() -> str:
    """
    Get all active flight anomalies/alerts.
    
    Returns:
        JSON string with alert information
    """
    tool = MCPTool("alerts.list_active")
    result = tool.call()
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    alerts = result.get("result", [])
    count = result.get("count", len(alerts))
    
    if count == 0:
        return "No active alerts. All flights appear normal."
    
    # Format alerts summary
    summary = f"Found {count} active alerts:\n"
    for i, alert in enumerate(alerts[:5], 1):  # Show first 5
        flight = alert.get("flight", {})
        summary += f"{i}. {alert.get('anomaly_type')} - {alert.get('description')}\n"
    
    if count > 5:
        summary += f"... and {count - 5} more alerts."
    
    return summary

