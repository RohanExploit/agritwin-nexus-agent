"""Four specialized Agro-Digital-Twin Sub-Agents under AgriTwin Orchestrator."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from .tools import FARM_HUBS, MANDI_HUBS, fetch_agro_microclimate, fetch_osrm_route

CROP_PROFILES = {
    "Strawberry": {"base_price_inr_ton": 145000, "spoilage_rate_per_hr": 0.018, "opt_moisture": 0.30, "blight_hum_thresh": 74},
    "Tomato": {"base_price_inr_ton": 28000, "spoilage_rate_per_hr": 0.011, "opt_moisture": 0.27, "blight_hum_thresh": 78},
    "Pomegranate": {"base_price_inr_ton": 86000, "spoilage_rate_per_hr": 0.004, "opt_moisture": 0.22, "blight_hum_thresh": 82},
    "Onion": {"base_price_inr_ton": 32000, "spoilage_rate_per_hr": 0.003, "opt_moisture": 0.20, "blight_hum_thresh": 80},
}


@dataclass
class AgroBusMessage:
    sender: str
    recipient: str
    phase: str
    content: str
    confidence: float


@dataclass
class AgroTwinContext:
    farm_hub: str
    crop: str
    cold_chain_enabled: bool
    microclimate: dict[str, Any] = field(default_factory=dict)
    pest_assessment: dict[str, Any] = field(default_factory=dict)
    mandi_routes: list[dict[str, Any]] = field(default_factory=list)
    dispatch_advice: dict[str, Any] = field(default_factory=dict)
    messages: list[AgroBusMessage] = field(default_factory=list)

    def emit(self, sender: str, recipient: str, phase: str, content: str, confidence: float = 0.93) -> None:
        self.messages.append(AgroBusMessage(sender, recipient, phase, content, round(confidence, 2)))


class AgroMicroclimateScout:
    """Sub-Agent 1: Polls Open-Meteo soil temperature, soil moisture, ET0 & humidity."""

    name = "AgroMicroclimateScout"

    def run(self, ctx: AgroTwinContext) -> None:
        coords = FARM_HUBS.get(ctx.farm_hub, list(FARM_HUBS.values())[0])
        ctx.microclimate = fetch_agro_microclimate(coords["lat"], coords["lon"])
        ctx.emit(
            self.name,
            "PestBlightRiskModeler",
            "SENSE-SOIL",
            f"Sampled {ctx.farm_hub}: Soil moisture={ctx.microclimate['soil_moisture']} m³/m³, ET₀={ctx.microclimate['daily_et0_mm']} mm/day, RH={ctx.microclimate['mean_humidity_pct']}%.",
            confidence=0.96,
        )


class PestBlightRiskModeler:
    """Sub-Agent 2: Computes fungal blight, heat stress, and irrigation deficit indices."""

    name = "PestBlightRiskModeler"

    def run(self, ctx: AgroTwinContext) -> None:
        mc = ctx.microclimate
        prof = CROP_PROFILES.get(ctx.crop, CROP_PROFILES["Tomato"])
        hum_excess = max(0.0, mc["mean_humidity_pct"] - prof["blight_hum_thresh"])
        rain_factor = mc["max_rain_prob_pct"] * 0.35
        blight_risk = round(min(98.0, 12.0 + hum_excess * 2.1 + rain_factor), 1)

        moisture_gap = round(prof["opt_moisture"] - mc["soil_moisture"], 3)
        irrigation_action = "Irrigate 12–18mm tonight" if moisture_gap > 0.04 else ("Hold irrigation (soil saturated)" if moisture_gap < -0.05 else "Soil moisture optimal")

        ctx.pest_assessment = {
            "blight_risk": blight_risk,
            "irrigation_action": irrigation_action,
            "moisture_gap": moisture_gap,
            "heat_stress": "ELEVATED" if mc["max_temp_c"] >= 34.0 else "LOW",
        }
        ctx.emit(
            self.name,
            "ColdChainRouteOptimizer",
            "MODEL-CROP",
            f"Crop `{ctx.crop}` blight risk={blight_risk}/100 | Heat={ctx.pest_assessment['heat_stress']} | {irrigation_action}.",
            confidence=0.92,
        )


class ColdChainRouteOptimizer:
    """Sub-Agent 3: Queries OSRM live highway routes and models Q10 spoilage vs mandi net margin."""

    name = "ColdChainRouteOptimizer"

    def run(self, ctx: AgroTwinContext) -> None:
        origin = FARM_HUBS.get(ctx.farm_hub, list(FARM_HUBS.values())[0])
        prof = CROP_PROFILES.get(ctx.crop, CROP_PROFILES["Tomato"])
        temp_c = ctx.microclimate["mean_temp_c"]
        # Q10 temperature acceleration factor when ambient transport vs refrigerated reefer
        q10_factor = 0.25 if ctx.cold_chain_enabled else (2.0 ** ((temp_c - 15.0) / 10.0))

        with ThreadPoolExecutor(max_workers=4) as pool:
            osrm_results = list(
                pool.map(lambda h: fetch_osrm_route(origin["lat"], origin["lon"], h["lat"], h["lon"]), MANDI_HUBS)
            )

        routes: list[dict[str, Any]] = []
        for hub, r in zip(MANDI_HUBS, osrm_results):
            spoilage_pct = round(min(45.0, prof["spoilage_rate_per_hr"] * r["duration_hr"] * q10_factor * 100.0), 2)
            gross_rev = prof["base_price_inr_ton"] * hub["price_factor"]
            freight_cost = r["distance_km"] * (38.0 if ctx.cold_chain_enabled else 22.0)
            net_margin = round(gross_rev * (1.0 - spoilage_pct / 100.0) - freight_cost, 0)
            routes.append(
                {
                    "mandi": hub["name"],
                    "distance_km": r["distance_km"],
                    "transit_hr": r["duration_hr"],
                    "spoilage_loss_pct": spoilage_pct,
                    "freight_inr_ton": round(freight_cost, 0),
                    "net_realization_inr_ton": net_margin,
                    "route_source": r["source"],
                }
            )

        routes.sort(key=lambda x: x["net_realization_inr_ton"], reverse=True)
        ctx.mandi_routes = routes
        best = routes[0]
        ctx.emit(
            self.name,
            "HarvestDispatchPlanner",
            "OPTIMIZE-LOGISTICS",
            f"Best net APMC route: {best['mandi']} ({best['distance_km']} km, {best['transit_hr']} hr, spoilage={best['spoilage_loss_pct']}%, net=₹{best['net_realization_inr_ton']:,.0f}/ton).",
            confidence=0.94,
        )


class HarvestDispatchPlanner:
    """Sub-Agent 4: Emits optimal harvest window & cold-chain dispatch schedule."""

    name = "HarvestDispatchPlanner"

    def run(self, ctx: AgroTwinContext) -> None:
        best = ctx.mandi_routes[0]
        rain_p = ctx.microclimate["max_rain_prob_pct"]
        window = "HARVEST EARLY MORNING (05:30–08:30 IST) BEFORE RAIN/HEAT" if rain_p > 55 or ctx.microclimate["max_temp_c"] > 33 else "OPTIMAL FULL-DAY HARVEST WINDOW"
        ctx.dispatch_advice = {
            "harvest_window": window,
            "recommended_mandi": best["mandi"],
            "net_margin_inr_ton": best["net_realization_inr_ton"],
            "cold_chain_mode": "Active Reefer (4°C)" if ctx.cold_chain_enabled else "Ambient Tarpaulin Truck",
        }
        ctx.emit(
            self.name,
            "AgriTwin Orchestrator",
            "DISPATCH",
            f"{window} → Dispatch to {best['mandi']} ({ctx.dispatch_advice['cold_chain_mode']}).",
            confidence=0.95,
        )
