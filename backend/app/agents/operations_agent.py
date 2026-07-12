from typing import Dict, Any, List

from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentType
from app.simulators.stadium_simulator import get_simulator
from app.rag.retriever import get_knowledge_retriever


class OperationsAgent(BaseAgent):
    """Natural-language operations copilot over crowd/transit/weather/staff/SOPs."""

    def __init__(self):
        super().__init__(AgentType.OPERATIONS)
        self.simulator = get_simulator()

    def get_system_prompt(self) -> str:
        return (
            "You are the ArenaMind Operations Copilot for FIFA World Cup 2026. Answer the operator's "
            "natural-language question using the gathered crowd, transit, weather, and staff data plus any "
            "SOP context. Format: (1) direct answer, (2) data analyzed, (3) specific recommended actions, "
            "(4) confidence. Be concise and authoritative."
        )

    async def gather_data(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        densities = self.simulator.get_gate_densities()
        transit = self.simulator.get_transit()
        weather = self.simulator.get_weather()
        staff = self._staff()

        narrative = self.simulator.generate_narrative()
        context_text = (
            f"Crowd narrative: {narrative}\n"
            "Gate densities:\n" + "\n".join(
                f"- {d['gate_id']}: {d['density_percentage']}% trend={d['trend']} wait~{d['estimated_wait_minutes']}min"
                for d in densities
            )
            + "\nTransit:\n" + "\n".join(
                f"- {t.line} @ {t.station}: {t.status.value} delay={t.delay_minutes}min" for t in transit
            )
            + f"\nWeather: {weather.condition.value} alert={weather.alert}\n"
            + f"Staff: {staff}"
        )

        sources = ["crowd_simulator", "transit_simulator", "weather_simulator", "staff_deployment"]
        recommended = []
        delayed = [t for t in transit if t.status.value in ("delayed", "crowded")]
        high = [d for d in densities if d["density_percentage"] > 70]
        if delayed:
            recommended.append(f"Queue increase correlates with {', '.join(t.line for t in delayed)} delays; expect normalization in ~15-18 min.")
        if high:
            recommended.append(f"Open additional express lanes / deploy stewards to {', '.join(d['gate_id'] for d in high)}.")
        if weather.condition.value in ("rain", "storm"):
            recommended.append("Reduce outdoor queue exposure; shelter prioritized at Gate F.")

        # Pull SOP context for ops
        try:
            retriever = await get_knowledge_retriever()
            docs = await retriever.search(payload.get("question", ""), role="operator", category="operations", top_k=2)
            if docs:
                context_text += "\nSOP excerpts:\n" + "\n".join(d["content"][:200] for d in docs)
                sources.append("sops")
        except Exception:
            pass

        return {
            "context_text": context_text,
            "data_sources": sources,
            "recommended_actions": recommended,
            "related_metrics": {"gate_count": len(densities), "high_density_count": len(high)},
            "tools_used": ["get_crowd_summary", "get_transit", "get_weather", "get_staff", "query_sops"],
        }

    def _staff(self) -> Dict[str, Any]:
        return {
            "gate_staff": {"gate_a": 8, "gate_b": 6, "gate_c": 5, "gate_d": 4, "gate_e": 4, "gate_f": 6},
            "roving_security": 24, "medical_teams": 4, "volunteers": 50,
        }
