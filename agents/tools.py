"""Keyless live agro-sensors: Open-Meteo Soil/ET0 Telemetry & OSRM Highway Routing."""

from __future__ import annotations

import math
from typing import Any

import requests

HEADERS = {"User-Agent": "AgriTwin-Nexus-Agent/1.0"}

FARM_HUBS = {
    "Satara (Strawberry / Tomato Belt)": {"lat": 17.6805, "lon": 74.0183},
    "Mahabaleshwar (High-Value Berry Hub)": {"lat": 17.9237, "lon": 73.6586},
    "Nashik (Niphad Onion / Grape Belt)": {"lat": 20.0750, "lon": 74.1050},
    "Baramati (Sugarcane / Pomegranate)": {"lat": 18.1517, "lon": 74.5777},
}

MANDI_HUBS = [
    {"name": "Pune Gultekdi Market Yard", "lat": 18.4900, "lon": 73.8680, "price_factor": 1.04},
    {"name": "Vashi APMC Navi Mumbai", "lat": 19.0760, "lon": 73.0050, "price_factor": 1.15},
    {"name": "Kolhapur Shahupuri APMC", "lat": 16.7050, "lon": 74.2433, "price_factor": 0.98},
    {"name": "Satara Local Cold-Storage Hub", "lat": 17.6914, "lon": 74.0009, "price_factor": 0.92},
]


def fetch_agro_microclimate(lat: float, lon: float, timeout: float = 5.5) -> dict[str, Any]:
    """Fetch live Open-Meteo soil temperature, soil moisture, humidity & evapotranspiration."""
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,soil_temperature_0cm,soil_moisture_0_to_1cm,et0_fao_evapotranspiration",
                "forecast_days": 2,
                "timezone": "auto",
            },
            headers=HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        h = resp.json().get("hourly", {})
        temps = [float(x or 25) for x in h.get("temperature_2m", [])[:24]]
        hum = [float(x or 60) for x in h.get("relative_humidity_2m", [])[:24]]
        rain_p = [float(x or 0) for x in h.get("precipitation_probability", [])[:24]]
        soil_t = [float(x or 24) for x in h.get("soil_temperature_0cm", [])[:24]]
        soil_m = [float(x or 0.25) for x in h.get("soil_moisture_0_to_1cm", [])[:24]]
        et0 = [float(x or 0.15) for x in h.get("et0_fao_evapotranspiration", [])[:24]]
        return {
            "mean_temp_c": round(sum(temps) / max(len(temps), 1), 1),
            "max_temp_c": round(max(temps, default=28.0), 1),
            "mean_humidity_pct": round(sum(hum) / max(len(hum), 1), 1),
            "max_rain_prob_pct": round(max(rain_p, default=0.0), 1),
            "soil_temp_c": round(sum(soil_t) / max(len(soil_t), 1), 1),
            "soil_moisture": round(sum(soil_m) / max(len(soil_m), 1), 3),
            "daily_et0_mm": round(sum(et0), 2),
            "source": "live-open-meteo-agro",
        }
    except Exception as exc:
        return {
            "mean_temp_c": 26.4,
            "max_temp_c": 31.2,
            "mean_humidity_pct": 68.0,
            "max_rain_prob_pct": 20.0,
            "soil_temp_c": 25.1,
            "soil_moisture": 0.24,
            "daily_et0_mm": 3.8,
            "source": f"agro-backup ({type(exc).__name__})",
        }


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def fetch_osrm_route(lat1: float, lon1: float, lat2: float, lon2: float, timeout: float = 4.5) -> dict[str, Any]:
    """Query OSRM live highway driving distance & duration; fallback to road-factor Haversine."""
    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
        resp = requests.get(url, params={"overview": "false"}, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        route = (resp.json().get("routes") or [{}])[0]
        dist_km = round(float(route.get("distance", 0)) / 1000.0, 1)
        dur_hr = round(float(route.get("duration", 0)) / 3600.0, 2)
        if dist_km <= 0:
            raise ValueError("Zero route")
        return {"distance_km": dist_km, "duration_hr": dur_hr, "source": "live-osrm-routing"}
    except Exception:
        crow = _haversine_km(lat1, lon1, lat2, lon2)
        dist_km = round(crow * 1.28, 1)
        dur_hr = round(dist_km / 48.0, 2)
        return {"distance_km": dist_km, "duration_hr": dur_hr, "source": "haversine-road-model"}
