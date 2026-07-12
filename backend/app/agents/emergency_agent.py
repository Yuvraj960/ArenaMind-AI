import math
from typing import Dict, Any, List

from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentType
from app.simulators.stadium_simulator import get_simulator


class EmergencyAgent(BaseAgent):
    """Emergency response plan generator. Renders exits, medical, security, evacuation
    routes, multilingual announcements, and estimated clearance time from static
    stadium resource data."""

    def __init__(self):
        super().__init__(AgentType.EMERGENCY)
        self.simulator = get_simulator()

    def get_system_prompt(self) -> str:
        return (
            "You are the ArenaMind Emergency Response Agent for FIFA World Cup 2026. "
            "Using the gathered scenario and resource data, write a precise, calm, directive "
            "emergency response plan. Include: immediate actions (0-60s), evacuation routes from "
            "the location, nearest medical/security/exit resources, staff assignments, multilingual "
            "public announcements, and estimated clearance time. Every second counts — be decisive. "
            "Reply in the same language as the incident details, defaulting to English."
        )

    async def gather_data(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        loc = payload.get("location", {})
        scenario_type = payload.get("type", "unknown")
        severity = payload.get("severity", "medium")
        lat = loc.get("lat", 40.7128)
        lng = loc.get("lng", -74.0060)

        exits = self._find_exits(lat, lng, count=5)
        medical = self._find_medical(lat, lng, count=3)
        security = self._find_security(lat, lng, count=3)
        crowd = self._crowd_nearby(lat, lng)

        context_text = (
            f"Scenario: {scenario_type} | Severity: {severity}\n"
            f"Location: ({lat:.4f}, {lng:.4f})\n"
            f"Nearby exits: " + ", ".join(f"{e['name']} ({e['distance_m']}m)" for e in exits) + "\n"
            f"Nearby medical: " + ", ".join(f"{m['name']} ({m['distance_m']}m)" for m in medical) + "\n"
            f"Nearby security: " + ", ".join(f"{s['name']} ({s['distance_m']}m)" for s in security) + "\n"
            f"Est. crowd at location: {crowd['total_people_nearby']} people; "
            f"evacuation feasibility: {crowd['evacuation_feasibility']}"
        )

        return {
            "context_text": context_text,
            "scenario_type": scenario_type,
            "severity": severity,
            "evacuation_routes": exits,
            "nearest_exits": exits,
            "nearest_medical": medical,
            "nearest_security": security,
            "assigned_staff": self._assign_staff(scenario_type),
            "announcements": self._announcements(scenario_type, severity),
            "estimated_clearance_time_min": self._clearance_time(scenario_type, crowd),
            "coordination_notes": "",
            "tools_used": ["get_nearest_exits", "get_nearest_medical", "get_nearest_security", "get_crowd_at_location"],
        }

    def _find_exits(self, lat: float, lng: float, count: int) -> List[Dict[str, Any]]:
        out = []
        for gate_id, gate in self.simulator.gates.items():
            d = self._haversine(lat, lng, gate.lat, gate.lng) * 1000
            out.append({
                "id": gate_id, "name": gate.name, "lat": gate.lat, "lng": gate.lng,
                "distance_m": round(d), "estimated_time_sec": int(d / 1.4),
                "accessible": "wheelchair" in gate.accessibility_features,
                "capacity": gate.capacity,
            })
        out.sort(key=lambda x: x["distance_m"])
        return out[:count]

    def _find_medical(self, lat: float, lng: float, count: int) -> List[Dict[str, Any]]:
        stations = [
            {"id": "med_a", "name": "Medical Station - Gate A", "lat": 40.7130, "lng": -74.0055, "type": "first_aid", "aed": True},
            {"id": "med_central", "name": "Central Medical Center", "lat": 40.7125, "lng": -74.0057, "type": "advanced", "aed": True, "ambulance": True},
            {"id": "aed_b", "name": "AED - Section North", "lat": 40.7135, "lng": -74.0058, "type": "aed_only"},
            {"id": "aed_c", "name": "AED - Section South", "lat": 40.7118, "lng": -74.0058, "type": "aed_only"},
        ]
        out = []
        for m in stations:
            d = self._haversine(lat, lng, m["lat"], m["lng"]) * 1000
            out.append({**m, "distance_m": round(d), "estimated_time_sec": int(d / 1.2)})
        out.sort(key=lambda x: x["distance_m"])
        return out[:count]

    def _find_security(self, lat: float, lng: float, count: int) -> List[Dict[str, Any]]:
        posts = [
            {"id": "sec_a", "name": "Security Post - Gate A", "lat": 40.7130, "lng": -74.0055, "personnel": 4},
            {"id": "sec_central", "name": "Central Security Command", "lat": 40.7125, "lng": -74.0057, "personnel": 10},
            {"id": "sec_roving", "name": "Roving Patrol", "lat": 40.7128, "lng": -74.0058, "personnel": 2},
        ]
        out = []
        for s in posts:
            d = self._haversine(lat, lng, s["lat"], s["lng"]) * 1000
            out.append({**s, "distance_m": round(d), "estimated_time_sec": int(d / 2.0)})
        out.sort(key=lambda x: x["distance_m"])
        return out[:count]

    def _crowd_nearby(self, lat: float, lng: float) -> Dict[str, Any]:
        total = 0
        for gate in self.simulator.gates.values():
            d = self._haversine(lat, lng, gate.lat, gate.lng) * 1000
            if d < 200:
                total += gate.current_count
        return {
            "total_people_nearby": total,
            "evacuation_feasibility": "high" if total < 3000 else "medium" if total < 10000 else "low",
        }

    def _assign_staff(self, scenario: str) -> List[Dict[str, Any]]:
        base = [
            {"role": "Incident Commander", "count": 1, "location": "Central Command"},
            {"role": "Security Lead", "count": 1, "location": "Nearest to incident"},
        ]
        if scenario in ("medical",):
            base.append({"role": "Medical Team", "count": 2, "location": "Dispatch to incident"})
            base.append({"role": "AED Paramedic", "count": 1, "location": "Nearest AED route"})
        elif scenario in ("fire", "evacuation"):
            base.append({"role": "Evacuation Wardens", "count": 4, "location": "All affected exits"})
            base.append({"role": "Fire Safety Officer", "count": 1, "location": "Incident site"})
        else:
            base.append({"role": "Security Team", "count": 4, "location": "Perimeter + interior"})
        return base

    def _announcements(self, scenario: str, severity: str) -> List[Dict[str, str]]:
        templates = {
            "medical": ("Medical emergency reported. Please clear the area and follow staff instructions.", "Medical emergency. Please cooperate with staff."),
            "fire": ("Fire reported. Evacuate calmly via the nearest exit. Do not use elevators.", "Fire incident in progress."),
            "suspicious_object": ("Security alert. Do not approach suspicious items. Follow staff directions.", "Security alert near your location."),
            "overcrowding": ("Crowd congestion ahead. Please use alternative gates as directed by staff.", "Congestion in this area."),
            "stampede": ("Emergency. Move calmly to exits. Do not push.", "Critical crowd safety notice."),
            "weather": ("Severe weather alert. Please move to covered areas immediately.", "Weather alert in effect."),
        }
        en, es = templates.get(scenario, templates["medical"])
        return [
            {"language": "en", "text": en},
            {"language": "es", "text": f"[ES] {es}"},
            {"language": "fr", "text": f"[FR] {en}"},
            {"language": "ar", "text": f"[AR] {en}"},
        ]

    def _clearance_time(self, scenario: str, crowd: Dict) -> int:
        base = {"medical": 12, "fire": 20, "suspicious_object": 25, "overcrowding": 15, "stampede": 30, "weather": 10}.get(scenario, 15)
        if crowd["evacuation_feasibility"] == "low":
            base = int(base * 1.5)
        return base

    def _haversine(self, lat1, lng1, lat2, lng2) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))