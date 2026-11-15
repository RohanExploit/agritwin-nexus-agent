"""Automated pytest suite for AgriTwin Nexus precision crop & cold-chain twin."""

from __future__ import annotations

from pathlib import Path

from agents.memory import AgroMemoryStore
from agents.orchestrator import AgriTwinOrchestrator
from agents.subagents import AgroTwinContext, ColdChainRouteOptimizer


def test_cold_chain_reduces_spoilage(monkeypatch) -> None:
    monkeypatch.setattr(
        "agents.subagents.fetch_osrm_route",
        lambda lat1, lon1, lat2, lon2: {"distance_km": 120.0, "duration_hr": 2.5, "source": "mock"},
    )
    opt = ColdChainRouteOptimizer()
    ctx_reefer = AgroTwinContext("Satara (Strawberry / Tomato Belt)", "Strawberry", True, microclimate={"mean_temp_c": 30.0})
    ctx_ambient = AgroTwinContext("Satara (Strawberry / Tomato Belt)", "Strawberry", False, microclimate={"mean_temp_c": 30.0})
    opt.run(ctx_reefer)
    opt.run(ctx_ambient)
    assert ctx_reefer.mandi_routes[0]["spoilage_loss_pct"] < ctx_ambient.mandi_routes[0]["spoilage_loss_pct"]


def test_full_twin_mocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "agents.subagents.fetch_agro_microclimate",
        lambda lat, lon: {
            "mean_temp_c": 26.0,
            "max_temp_c": 30.0,
            "mean_humidity_pct": 80.0,
            "max_rain_prob_pct": 40.0,
            "soil_temp_c": 24.0,
            "soil_moisture": 0.23,
            "daily_et0_mm": 4.1,
            "source": "mock",
        },
    )
    monkeypatch.setattr(
        "agents.subagents.fetch_osrm_route",
        lambda lat1, lon1, lat2, lon2: {"distance_km": 110.0, "duration_hr": 2.2, "source": "mock"},
    )
    out = AgriTwinOrchestrator(AgroMemoryStore(tmp_path / "agro.json")).run_twin(gemini_key="", groq_key="")
    assert len(out["messages"]) == 5
    assert len(out["mandi_routes"]) == 4
    assert out["memory"]["total_simulations"] == 1
