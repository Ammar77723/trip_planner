"""
Anomaly detection for flight data.
Simple rule-based detection for:
- Low speed at high altitude
- Stationary for too long
- Sudden altitude drops
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

# Thresholds for anomaly detection
LOW_SPEED_THRESHOLD = 50  # m/s (180 km/h)
HIGH_ALTITUDE_THRESHOLD = 8000  # meters
STATIONARY_VELOCITY_THRESHOLD = 5  # m/s (18 km/h)
MIN_ALTITUDE_FOR_STATIONARY = 1000  # meters (below this, on ground is normal)
SUDDEN_ALTITUDE_DROP_THRESHOLD = 1000  # meters per minute (if we had history)

def detect_anomalies(flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect anomalies in flight data.
    
    Args:
        flights: List of flight dictionaries with fields like:
            - callsign, icao24, latitude, longitude
            - baro_altitude, velocity, vertical_rate
            - on_ground, origin_country
    
    Returns:
        List of anomaly dictionaries with:
            - flight: flight data
            - anomaly_type: type of anomaly
            - severity: "low", "medium", "high"
            - description: human-readable description
    """
    alerts = []
    
    for flight in flights:
        if not isinstance(flight, dict):
            continue
        
        # Extract flight data
        callsign = flight.get("callsign", "").strip() if flight.get("callsign") else "UNKNOWN"
        icao24 = flight.get("icao24", "UNKNOWN")
        altitude = flight.get("baro_altitude")
        velocity = flight.get("velocity")
        vertical_rate = flight.get("vertical_rate")
        on_ground = flight.get("on_ground", False)
        
        # Skip if essential data is missing
        if altitude is None or velocity is None:
            continue
        
        # Convert altitude from meters (if needed)
        if altitude < 0:
            altitude = None
        
        # Anomaly 1: Low speed at high altitude
        if altitude and altitude > HIGH_ALTITUDE_THRESHOLD:
            if velocity and velocity < LOW_SPEED_THRESHOLD:
                alerts.append({
                    "flight": {
                        "callsign": callsign,
                        "icao24": icao24,
                        "altitude": altitude,
                        "velocity": velocity
                    },
                    "anomaly_type": "low_speed_high_altitude",
                    "severity": "high",
                    "description": f"Flight {callsign} is flying at low speed ({velocity:.1f} m/s) at high altitude ({altitude:.1f} m). This may indicate an issue."
                })
        
        # Anomaly 2: Stationary at altitude (not on ground)
        if not on_ground and altitude and altitude > MIN_ALTITUDE_FOR_STATIONARY:
            if velocity and velocity < STATIONARY_VELOCITY_THRESHOLD:
                alerts.append({
                    "flight": {
                        "callsign": callsign,
                        "icao24": icao24,
                        "altitude": altitude,
                        "velocity": velocity
                    },
                    "anomaly_type": "stationary_at_altitude",
                    "severity": "high",
                    "description": f"Flight {callsign} appears stationary (velocity: {velocity:.1f} m/s) at altitude {altitude:.1f} m. This is unusual."
                })
        
        # Anomaly 3: Rapid descent
        if vertical_rate is not None and vertical_rate < -20:  # Descending faster than 20 m/s
            alerts.append({
                "flight": {
                    "callsign": callsign,
                    "icao24": icao24,
                    "altitude": altitude,
                    "vertical_rate": vertical_rate
                },
                "anomaly_type": "rapid_descent",
                "severity": "medium",
                "description": f"Flight {callsign} is descending rapidly (vertical rate: {vertical_rate:.1f} m/s)."
            })
        
        # Anomaly 4: Very high altitude (potential issue)
        if altitude and altitude > 12000:  # Above 12km
            if velocity and velocity > 300:  # Very fast
                alerts.append({
                    "flight": {
                        "callsign": callsign,
                        "icao24": icao24,
                        "altitude": altitude,
                        "velocity": velocity
                    },
                    "anomaly_type": "extreme_altitude_speed",
                    "severity": "low",
                    "description": f"Flight {callsign} is at extreme altitude ({altitude:.1f} m) with high speed ({velocity:.1f} m/s)."
                })
    
    return alerts

