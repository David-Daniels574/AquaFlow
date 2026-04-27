# utils.py
from datetime import datetime, timedelta
from models import WaterReading
import math
import requests

def get_road_metrics(lat1, lon1, lat2, lon2):
    """
    Calculate actual driving distance and duration using OSRM (OpenStreetMap).
    Returns: (distance_km, duration_minutes)
    """
    # OSRM requires coordinates in (longitude, latitude) format
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    
    try:
        response = requests.get(url, timeout=5) # 5 second timeout
        if response.status_code == 200:
            data = response.json()
            if data.get("routes"):
                # OSRM returns distance in meters and duration in seconds
                meters = data["routes"][0]["distance"]
                seconds = data["routes"][0]["duration"]
                
                distance_km = meters / 1000
                duration_min = seconds / 60
                
                return distance_km, duration_min
    except Exception as e:
        print(f"Error fetching OSRM data: {e}")
        
    # Fallback to Haversine if API fails
    print("Falling back to Haversine calculation...")
    return haversine_fallback(lat1, lon1, lat2, lon2)

def haversine_fallback(lat1, lon1, lat2, lon2):
    """
    Fallback Haversine calculation if OSM API is down.
    """
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    # Estimate time: Assume 30km/h average speed in city for straight line approximation
    duration_min = (distance / 30) * 60 
    return distance, duration_min

def calculate_eta(distance):
    """
    Calculate estimated time of arrival in minutes (assume 40 km/h speed).
    """
    speed = 40  # km/h
    time_hours = distance / speed
    return time_hours * 60  # minutes

def get_consumption_reports(user_id, period='daily'):
    """
    Generate consumption reports for specified period.
    """
    now = datetime.utcnow()
    if period == 'daily':
        start = now - timedelta(days=1)
        divisor = 1
    elif period == 'weekly':
        start = now - timedelta(weeks=1)
        divisor = 7
    elif period == 'monthly':
        start = now - timedelta(days=30)
        divisor = 30
    else:
        return {'error': 'Invalid period'}
    
    readings = WaterReading.query.filter(
        WaterReading.user_id == user_id,
        WaterReading.timestamp >= start
    ).order_by(WaterReading.timestamp).all()
    
    if not readings:
        return {'total': 0, 'average': 0}
    
    total = readings[-1].reading - readings[0].reading
    average = total / divisor
    return {'total': total, 'average': average}