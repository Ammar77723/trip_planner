"""
MCP Server for Flight Data
Exposes flight data as MCP tools for agent access.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import requests
import json
import os
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.anomaly_detector import detect_anomalies

app = FastAPI(title="Flight Data MCP Server", version="1.0.0")

# Configuration
WEBHOOK_BASE_URL = "http://localhost:5678/webhook"
FALLBACK_DATA_DIR = "C:/Users/hp/Documents"

# Request/Response models
class RegionRequest(BaseModel):
    region: str

class CallsignRequest(BaseModel):
    callsign: str
    region: Optional[str] = None

class AlertRequest(BaseModel):
    pass

def get_flight_data(region: str = "data") -> Optional[Dict]:
    """
    Get flight data from webhook, fallback to file.
    
    Args:
        region: Region identifier (e.g., "data", "region1")
    
    Returns:
        Dictionary containing flight data or None if unavailable
    """
    # Try webhook first
    webhook_url = f"{WEBHOOK_BASE_URL}/latest-{region}"
    try:
        response = requests.get(webhook_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Data fetched from webhook: {webhook_url}")
            return data
    except requests.exceptions.RequestException as e:
        print(f"⚠ Webhook failed ({webhook_url}): {e}")
    except Exception as e:
        print(f"⚠ Webhook error: {e}")
    
    # Fallback to file
    file_path = f"{FALLBACK_DATA_DIR}/{region}_latest.json"
    # Also try with forward slashes
    file_path_alt = file_path.replace("\\", "/")
    
    for path in [file_path, file_path_alt]:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✓ Data loaded from file: {path}")
                    return data
            except Exception as e:
                print(f"⚠ File read error ({path}): {e}")
    
    print(f"✗ No data available for region: {region}")
    return None

# MCP Tool 1: List region snapshot
@app.post("/mcp/tools/flights.list_region_snapshot")
async def list_region_snapshot(request: RegionRequest):
    """
    Returns the most recent snapshot for a region.
    
    MCP Tool: flights.list_region_snapshot
    """
    data = get_flight_data(request.region)
    
    if not data:
        raise HTTPException(
            status_code=404, 
            detail=f"No data available for region: {request.region}"
        )
    
    return {
        "tool": "flights.list_region_snapshot",
        "result": data,
        "timestamp": datetime.now().isoformat(),
        "region": request.region
    }

# MCP Tool 2: Get flight by callsign
@app.post("/mcp/tools/flights.get_by_callsign")
async def get_by_callsign(request: CallsignRequest):
    """
    Finds the latest record for a given flight callsign.
    
    MCP Tool: flights.get_by_callsign
    """
    region = request.region or "data"
    data = get_flight_data(region)
    
    if not data:
        raise HTTPException(status_code=404, detail="No data available")
    
    # Extract flights from data structure
    flights = data.get("flights", [])
    if not flights:
        # Try alternative structure
        if isinstance(data, list):
            flights = data
        elif "states" in data:
            # If data is in OpenSky format
            flights = data["states"]
    
    # Search for flight by callsign
    target_callsign = request.callsign.strip().upper()
    
    for flight in flights:
        if isinstance(flight, dict):
            callsign = flight.get("callsign", "")
            if callsign:
                callsign = callsign.strip().upper()
                if callsign == target_callsign:
                    return {
                        "tool": "flights.get_by_callsign",
                        "result": flight,
                        "timestamp": datetime.now().isoformat(),
                        "callsign": request.callsign
                    }
        elif isinstance(flight, list) and len(flight) > 1:
            # OpenSky format: [icao24, callsign, ...]
            callsign = flight[1].strip().upper() if len(flight) > 1 and flight[1] else ""
            if callsign == target_callsign:
                # Convert to dict format
                flight_dict = {
                    "icao24": flight[0] if len(flight) > 0 else None,
                    "callsign": flight[1] if len(flight) > 1 else None,
                    "origin_country": flight[2] if len(flight) > 2 else None,
                    "time_position": flight[3] if len(flight) > 3 else None,
                    "last_contact": flight[4] if len(flight) > 4 else None,
                    "longitude": flight[5] if len(flight) > 5 else None,
                    "latitude": flight[6] if len(flight) > 6 else None,
                    "baro_altitude": flight[7] if len(flight) > 7 else None,
                    "on_ground": flight[8] if len(flight) > 8 else None,
                    "velocity": flight[9] if len(flight) > 9 else None,
                    "true_track": flight[10] if len(flight) > 10 else None,
                    "vertical_rate": flight[11] if len(flight) > 11 else None,
                }
                return {
                    "tool": "flights.get_by_callsign",
                    "result": flight_dict,
                    "timestamp": datetime.now().isoformat(),
                    "callsign": request.callsign
                }
    
    raise HTTPException(
        status_code=404, 
        detail=f"Flight with callsign '{request.callsign}' not found in region '{region}'"
    )

# MCP Tool 3: List active alerts
@app.post("/mcp/tools/alerts.list_active")
async def list_active_alerts(request: AlertRequest):
    """
    Returns currently flagged anomalies.
    
    MCP Tool: alerts.list_active
    """
    # Get data from default region
    data = get_flight_data("data")
    
    if not data:
        return {
            "tool": "alerts.list_active",
            "result": [],
            "timestamp": datetime.now().isoformat(),
            "message": "No data available for anomaly detection"
        }
    
    # Extract flights
    flights = data.get("flights", [])
    if not flights:
        if isinstance(data, list):
            flights = data
        elif "states" in data:
            flights = data["states"]
    
    # Convert OpenSky format to dict if needed
    processed_flights = []
    for flight in flights:
        if isinstance(flight, dict):
            processed_flights.append(flight)
        elif isinstance(flight, list) and len(flight) > 1:
            # Convert OpenSky array format to dict
            processed_flights.append({
                "icao24": flight[0] if len(flight) > 0 else None,
                "callsign": flight[1] if len(flight) > 1 else None,
                "origin_country": flight[2] if len(flight) > 2 else None,
                "time_position": flight[3] if len(flight) > 3 else None,
                "last_contact": flight[4] if len(flight) > 4 else None,
                "longitude": flight[5] if len(flight) > 5 else None,
                "latitude": flight[6] if len(flight) > 6 else None,
                "baro_altitude": flight[7] if len(flight) > 7 else None,
                "on_ground": flight[8] if len(flight) > 8 else None,
                "velocity": flight[9] if len(flight) > 9 else None,
                "true_track": flight[10] if len(flight) > 10 else None,
                "vertical_rate": flight[11] if len(flight) > 11 else None,
            })
    
    # Detect anomalies
    alerts = detect_anomalies(processed_flights)
    
    return {
        "tool": "alerts.list_active",
        "result": alerts,
        "count": len(alerts),
        "timestamp": datetime.now().isoformat()
    }

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "MCP Flight Data Server",
        "timestamp": datetime.now().isoformat()
    }

# MCP tools list endpoint (for discovery)
@app.get("/mcp/tools")
async def list_tools():
    """List all available MCP tools."""
    return {
        "tools": [
            {
                "name": "flights.list_region_snapshot",
                "description": "Returns the most recent snapshot for a region",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "Region identifier (e.g., 'data', 'region1')"
                        }
                    },
                    "required": ["region"]
                }
            },
            {
                "name": "flights.get_by_callsign",
                "description": "Finds the latest record for a given flight callsign",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "callsign": {
                            "type": "string",
                            "description": "Flight callsign (e.g., 'SWR7YT')"
                        },
                        "region": {
                            "type": "string",
                            "description": "Optional region identifier"
                        }
                    },
                    "required": ["callsign"]
                }
            },
            {
                "name": "alerts.list_active",
                "description": "Returns currently flagged anomalies",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Flight Data MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "tools": "/mcp/tools",
            "list_region_snapshot": "/mcp/tools/flights.list_region_snapshot",
            "get_by_callsign": "/mcp/tools/flights.get_by_callsign",
            "list_active_alerts": "/mcp/tools/alerts.list_active"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting MCP Server on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

