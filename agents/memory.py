"""Model-based persistent memory for AgriTwin Nexus crop & cold-chain runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_STATE: dict[str, Any] = {
    "agent_name": "AgriTwin Harvest & Cold-Chain Orchestrator",
    "twin_history": [],
    "total_simulations": 0,
    "last_run_utc": None,
}


class AgroMemoryStore:
    """Stores historical crop blight risk, irrigation deficit, and optimal mandi dispatches."""

    def __init__(self, state_path: Path | str | None = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.path = Path(state_path) if state_path else base_dir / "state" / "agritwin_memory.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return json.loads(json.dumps(DEFAULT_STATE))
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for key, val in DEFAULT_STATE.items():
                data.setdefault(key, json.loads(json.dumps(val)))
            return data
        except Exception:
            return json.loads(json.dumps(DEFAULT_STATE))

    def save(self, state: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def update_after_run(
        self,
        farm_hub: str,
        crop: str,
        blight_risk: float,
        best_mandi: str,
        net_margin_inr: float,
        summary: str,
    ) -> dict[str, Any]:
        state = self.load()
        now_iso = datetime.now(timezone.utc).isoformat()
        state["total_simulations"] = int(state.get("total_simulations", 0)) + 1
        state["last_run_utc"] = now_iso
        state["twin_history"].append(
            {
                "timestamp_utc": now_iso,
                "farm_hub": farm_hub,
                "crop": crop,
                "blight_risk": round(blight_risk, 1),
                "best_mandi": best_mandi,
                "net_margin_inr_per_ton": round(net_margin_inr, 0),
                "summary": summary[:200],
            }
        )
        state["twin_history"] = state["twin_history"][-30:]
        self.save(state)
        return state
