"""Lead AgriTwin Harvest & Cold-Chain Orchestrator."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .llm_router import SynthesisResult, synthesize_with_fallback
from .memory import AgroMemoryStore
from .subagents import (
    AgroMicroclimateScout,
    AgroTwinContext,
    ColdChainRouteOptimizer,
    HarvestDispatchPlanner,
    PestBlightRiskModeler,
)


def _universal_agro_fallback(ctx: AgroTwinContext) -> str:
    best = ctx.mandi_routes[0] if ctx.mandi_routes else {}
    return (
        f"### AgriTwin Harvest & Cold-Chain Twin Brief (`{ctx.crop}` · `{ctx.farm_hub}`)\n"
        f"- **Microclimate & Irrigation**: Soil moisture `{ctx.microclimate.get('soil_moisture', 0)} m³/m³`, ET₀ `{ctx.microclimate.get('daily_et0_mm', 0)} mm/day` → *{ctx.pest_assessment.get('irrigation_action', '')}*.\n"
        f"- **Blight & Canopy Risk**: `{ctx.pest_assessment.get('blight_risk', 0)}/100` (Heat Stress: `{ctx.pest_assessment.get('heat_stress', 'LOW')}`).\n"
        f"- **OSRM Cold-Chain Winner**: Dispatch to **{best.get('mandi', 'N/A')}** (`{best.get('distance_km', 0)} km`, `{best.get('transit_hr', 0)} hr`, Spoilage `{best.get('spoilage_loss_pct', 0)}%`, Net `₹{best.get('net_realization_inr_ton', 0):,.0f}/ton`)."
    )


class AgriTwinOrchestrator:
    """Goal-Based + Model-Based + Utility-Based Precision Agriculture & Logistics Agent."""

    def __init__(self, memory_store: AgroMemoryStore | None = None) -> None:
        self.memory = memory_store or AgroMemoryStore()
        self.subagents = [
            AgroMicroclimateScout(),
            PestBlightRiskModeler(),
            ColdChainRouteOptimizer(),
            HarvestDispatchPlanner(),
        ]

    def run_twin(
        self,
        farm_hub: str = "Satara (Strawberry / Tomato Belt)",
        crop: str = "Strawberry",
        cold_chain_enabled: bool = True,
        gemini_key: str | None = None,
        groq_key: str | None = None,
    ) -> dict[str, Any]:
        ctx = AgroTwinContext(farm_hub=farm_hub, crop=crop, cold_chain_enabled=cold_chain_enabled)
        ctx.emit(
            "AgriTwin Orchestrator",
            "AgroMicroclimateScout",
            "DELEGATE",
            f"Launching soil-to-mandi digital twin for `{crop}` at `{farm_hub}` (reefer={cold_chain_enabled}).",
            confidence=0.98,
        )

        for agent in self.subagents:
            agent.run(ctx)

        prompt = (
            f"You are AgriTwin Precision Agriculture Orchestrator. Summarize this farm-to-mandi digital twin run in 3 crisp bullets "
            f"(Irrigation/Soil, Blight Protection, Optimal APMC Route) under 110 words.\n"
            f"Microclimate: {ctx.microclimate}\nPest: {ctx.pest_assessment}\nTop Routes: {ctx.mandi_routes[:2]}"
        )
        synthesis: SynthesisResult = synthesize_with_fallback(
            prompt=prompt,
            system_instruction="Be practical for Indian agronomy and cold-chain logistics.",
            universal_fallback_fn=lambda: _universal_agro_fallback(ctx),
            gemini_key=gemini_key,
            groq_key=groq_key,
        )

        best = ctx.mandi_routes[0]
        updated_state = self.memory.update_after_run(
            farm_hub=farm_hub,
            crop=crop,
            blight_risk=ctx.pest_assessment["blight_risk"],
            best_mandi=best["mandi"],
            net_margin_inr=best["net_realization_inr_ton"],
            summary=synthesis.text,
        )

        return {
            "farm_hub": farm_hub,
            "crop": crop,
            "microclimate": ctx.microclimate,
            "pest_assessment": ctx.pest_assessment,
            "mandi_routes": ctx.mandi_routes,
            "dispatch_advice": ctx.dispatch_advice,
            "messages": [asdict(m) for m in ctx.messages],
            "synthesis": asdict(synthesis),
            "memory": updated_state,
        }
