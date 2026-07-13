from fastapi import APIRouter
import uuid

from app.models.schemas import EmergencyScenario, EmergencyResponse
from app.agents.emergency_agent import EmergencyAgent
from app.agents.base_agent import AgentRequest
from app.models.schemas import AgentType

router = APIRouter()
emergency_agent = EmergencyAgent()


@router.post("/respond", response_model=EmergencyResponse)
async def respond_to_emergency(scenario: EmergencyScenario):
    """
    Generate an emergency response plan for a reported incident: nearest exits,
    medical/security resources, evacuation routes, staff assignments, multilingual
    announcements, and estimated clearance time.
    """
    scenario_id = str(uuid.uuid4())

    try:
        result = await emergency_agent.execute(AgentRequest(
            agent_type=AgentType.EMERGENCY,
            payload={
                "type": scenario.type,
                "location": scenario.location.model_dump(),
                "severity": scenario.severity,
                "details": scenario.details,
                "reported_by": scenario.reported_by,
                "timestamp": scenario.timestamp.isoformat(),
            },
        ))
        data = result.result
        text = data.get("response", "") or str(data)

        return EmergencyResponse(
            success=True,
            scenario_id=scenario_id,
            scenario_type=scenario.type,
            severity=scenario.severity,
            immediate_actions=_extract_actions(text),
            evacuation_routes=data.get("evacuation_routes", []),
            nearest_exits=data.get("nearest_exits", []),
            nearest_medical=data.get("nearest_medical", []),
            nearest_security=data.get("nearest_security", []),
            assigned_staff=data.get("assigned_staff", []),
            announcements=_build_announcements(scenario),
            estimated_clearance_time_min=data.get("estimated_clearance_time_min", 15),
            coordination_notes=text,
        )
    except Exception as e:
        return EmergencyResponse(
            success=False,
            scenario_id=scenario_id,
            scenario_type=scenario.type,
            severity=scenario.severity,
            immediate_actions=["Activate manual emergency protocols immediately"],
            evacuation_routes=[],
            nearest_exits=[],
            nearest_medical=[],
            nearest_security=[],
            assigned_staff=[],
            announcements=_build_announcements(scenario),
            estimated_clearance_time_min=0,
            coordination_notes=f"Automated response failed: {str(e)}. Fall back to manual SOPs.",
        )


def _extract_actions(text: str):
    """Pull bulleted action lines from the LLM coordination notes as a fallback."""
    actions = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(("- ", "* ", "• ")) or (line and line[0].isdigit() and "." in line[:3]):
            actions.append(line.lstrip("-*• 0123456789."))
    return actions[:10] or ["Secure the scene", "Dispatch nearest medical/security", "Clear evacuation routes"]


def _build_announcements(scenario: EmergencyScenario):
    """Multilingual public announcement templates for the incident."""
    base_en = {
        "medical": "Medical emergency reported. Please clear the area and follow staff instructions.",
        "fire": "Fire reported. Evacuate calmly via the nearest exit. Do not use elevators.",
        "suspicious_object": "Security alert. Do not approach or touch any suspicious items. Follow staff directions.",
        "overcrowding": "Crowd congestion ahead. Please use alternative gates directed by staff.",
        "stampede": "Emergency. Move calmly to exits. Do not push.",
        "weather": "Severe weather alert. Please move to covered areas immediately.",
        "security": "Security incident. Follow staff and official instructions immediately.",
    }
    msg = base_en.get(scenario.type, "Emergency reported. Follow staff instructions.")
    return [
        {"language": "en", "text": msg},
        {"language": "es", "text": f"[ES] {msg}"},
        {"language": "fr", "text": f"[FR] {msg}"},
        {"language": "ar", "text": f"[AR] {msg}"},
    ]