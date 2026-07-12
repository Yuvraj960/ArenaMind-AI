import math
from typing import Dict, Any, List

from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentType
from app.simulators.stadium_simulator import get_simulator


class NavigationAgent(BaseAgent):
    """Intent-based dynamic routing (not shortest-path). Reroutes around simulated
    congestion and honors accessibility constraints — accessibility is a parameter,
    never a bolt-on (per CLAUDE.md rule 7)."""

    def __init__(self):
        super().__init__(AgentType.NAVIGATION)
        self.simulator = get_simulator()

    def get_system_prompt(self) -> str:
        return (
            "You are the ArenaMind Navigation Agent for FIFA World Cup 2026. Using the gathered "
            "crowd densities, weather, and computed route, write a clear, short, human routing answer. "
            "Always state: chosen gate, estimated time, WHY it was chosen (crowd avoidance / accessibility "
            "/ weather), and one alternative. Respect accessibility needs (wheelchair → Gate F). Reply in "
            "the user's language."
        )

    async def gather_data(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        density_map = {d["gate_id"]: d for d in self.simulator.get_gate_densities()}
        weather = self.simulator.get_weather()

        route_info = self._compute_route(payload, density_map)
        tools = ["get_gate_densities", "get_weather", "calculate_route"]

        context_text = (
            f"Current gate densities:\n" + "\n".join(
                f"- {d['gate_name']}: {d['density_percentage']}% (trend {d['trend']})"
                for d in self.simulator.get_gate_densities()
            )
            + f"\nWeather: {weather.condition.value}, alert={weather.alert}\n"
            + f"Computed primary route: {route_info['primary_route'].get('via_gate_name')} "
            f"({route_info['primary_route'].get('estimated_time_sec')}s, "
            f"{route_info['primary_route'].get('total_distance_m')}m)\n"
            f"Accessibility needs: {payload.get('accessibility_needs', [])}"
        )

        return {
            "context_text": context_text,
            "primary_route": route_info["primary_route"],
            "alternatives": route_info["alternatives"],
            "crowd_warnings": route_info["crowd_warnings"],
            "accessibility_notes": route_info["accessibility_notes"],
            "tools_used": tools,
        }

    def _compute_route(self, payload: Dict[str, Any], density_map: Dict[str, Dict]) -> Dict[str, Any]:
        origin = payload.get("origin", {})
        destination = payload.get("destination", {})
        accessibility = list(payload.get("accessibility_needs", []))
        avoid_crowds = payload.get("avoid_crowds", True)
        prefer_covered = payload.get("prefer_covered", False)

        scored = []
        for gate_id, gate in self.simulator.gates.items():
            if gate.status != "open":
                continue
            score = 100.0
            if avoid_crowds:
                density = density_map.get(gate_id, {}).get("density_percentage", 0)
                score -= density * 0.5
            if "wheelchair" in accessibility and "wheelchair" in gate.accessibility_features:
                score += 30
            if "avoid_stairs" in accessibility and "express" in gate.accessibility_features:
                score += 20
            if "low_mobility" in accessibility and "priority" in gate.accessibility_features:
                score += 25
            if prefer_covered and "express" in gate.accessibility_features:
                score += 10
            scored.append({"gate": gate, "score": score})

        scored.sort(key=lambda x: x["score"], reverse=True)
        primary = scored[0]["gate"] if scored else list(self.simulator.gates.values())[0]

        primary_route = self._route_obj(origin, destination, primary, accessibility)
        alternatives = [self._route_obj(origin, destination, s["gate"], accessibility) for s in scored[1:3]]

        warnings = []
        for gid, d in density_map.items():
            if d["density_percentage"] > 80:
                warnings.append(f"⚠️ {d['gate_name']} at {d['density_percentage']}% — significant delays")
            elif d["density_percentage"] > 60:
                warnings.append(f"⚠️ {d['gate_name']} at {d['density_percentage']}% — moderate delays")

        notes = self._accessibility_notes(accessibility, primary)

        return {
            "primary_route": primary_route,
            "alternatives": alternatives,
            "crowd_warnings": warnings,
            "accessibility_notes": notes,
        }

    def _route_obj(self, origin, destination, gate, accessibility) -> Dict[str, Any]:
        speed = 1.2 if "wheelchair" in accessibility else 1.4
        d_o = self._haversine(origin.get("lat", 0), origin.get("lng", 0), gate.lat, gate.lng) * 1000
        d_d = self._haversine(destination.get("lat", 0), destination.get("lng", 0), gate.lat, gate.lng) * 1000
        total = d_o + d_d
        return {
            "origin": origin,
            "destination": destination,
            "via_gate": gate.gate_id,
            "via_gate_name": gate.name,
            "instructions": [
                f"Walk from {origin.get('label', 'current location')} to {gate.name} (~{int(d_o)}m)",
                f"Enter through {gate.name}",
                f"Proceed to {destination.get('label', 'destination')} (~{int(d_d)}m)",
            ],
            "total_distance_m": round(total),
            "estimated_time_sec": int(total / speed),
            "accessible": "wheelchair" in gate.accessibility_features,
            "crowd_density": gate.current_count / gate.capacity if gate.capacity else 0,
            "reason": f"Chosen for accessibility/crowd balance (features: {gate.accessibility_features})",
        }

    def _accessibility_notes(self, needs: List[str], gate) -> List[str]:
        notes = []
        if "wheelchair" in needs:
            notes.append("✅ Wheelchair access" if "wheelchair" in gate.accessibility_features
                         else "⚠️ Limited wheelchair access")
        if "avoid_stairs" in needs:
            notes.append("✅ Elevator/ramp" if "express" in gate.accessibility_features else "⚠️ May include stairs")
        if "visual_impairment" in needs:
            notes.append("Tactile guidance available")
        if "hearing_impairment" in needs:
            notes.append("Visual signage available")
        return notes

    def _haversine(self, lat1, lng1, lat2, lng2) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))
