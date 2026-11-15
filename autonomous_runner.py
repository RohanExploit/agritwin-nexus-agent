"""Headless autonomous runner for scheduled AgriTwin microclimate & mandi sweeps."""

from __future__ import annotations

import json

from agents.orchestrator import AgriTwinOrchestrator


def main() -> None:
    res = AgriTwinOrchestrator().run_twin()
    print(
        json.dumps(
            {
                "farm_hub": res["farm_hub"],
                "crop": res["crop"],
                "blight_risk": res["pest_assessment"]["blight_risk"],
                "recommended_mandi": res["dispatch_advice"]["recommended_mandi"],
                "provider": res["synthesis"]["provider"],
                "total_simulations": res["memory"]["total_simulations"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
