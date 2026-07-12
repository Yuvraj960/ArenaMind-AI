from typing import Dict, Any, List

from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentType
from app.simulators.stadium_simulator import get_simulator


class CrowdAgent(BaseAgent):
    """Turns raw crowd counts into GenAI narrative summaries + recommendations."""

    def __init__(self):
        super().__init__(AgentType.CROWD)
        self.simulator = get_simulator()

    def get_system_prompt(self) -> str:
        return (
            "You are the ArenaMind Crowd Intelligence Agent for FIFA World Cup 2026. Using the gathered "
            "gate densities, trends, transit and weather, write a natural-language crowd-intelligence "
            "summary. Flag congestion likely within 15-30 minutes and recommend specific corrective actions "
            "(redirect to named gates, add staff). Be specific and actionable."
        )

    async def gather_data(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        densities = self.simulator.get_gate_densities()
        transit = self.simulator.get_transit()
        weather = self.simulator.get_weather()

        hot = [d for d in densities if d["density_percentage"] > 70]
        rising = [d for d in densities if d["trend"] == "increasing"]
        delayed = [t for t in transit if t.status.value in ("delayed", "crowded")]

        context_text = (
            "Gate densities:\n" + "\n".join(
                f"- {d['gate_name']}: {d['density_percentage']}% (trend {d['trend']}, wait ~{d['estimated_wait_minutes']}min)"
                for d in densities
            )
            + "\nTransit: " + ", ".join(f"{t.line}={t.status.value}" for t in transit)
            + f"\nWeather: {weather.condition.value} alert={weather.alert}"
        )

        recommended = []
        if any(d["gate_id"] == "gate_b" and d["density_percentage"] > 70 for d in hot):
            recommended.append("Redirect Gate B arrivals to Gate D (lower density, accessible).")
        if rising:
            recommended.append(f"Pre-position stewards near {', '.join(g['gate_name'] for g in rising[:3])}.")
        if delayed:
            recommended.append("Expect arrival surges post-transit-delay; keep Gate A/D express lanes open.")

        return {
            "context_text": context_text,
            "data_sources": ["crowd_simulator", "transit_simulator", "weather_simulator"],
            "recommended_actions": recommended,
            "trends": {"high_density_gates": [h["gate_id"] for h in hot], "rising": [g["gate_id"] for g in rising]},
            "tools_used": ["get_gate_densities", "get_transit", "get_weather"],
        }
