from fastapi import APIRouter, HTTPException
from typing import Optional
import uuid

from app.models.schemas import (
    NavigationRequest,
    NavigationResponse,
    Location,
    Route,
    RoutePoint,
    AccessibilityNeed,
)
from app.agents.navigation_agent import NavigationAgent
from app.agents.base_agent import AgentRequest
from app.models.schemas import AgentType

router = APIRouter()
navigation_agent = NavigationAgent()


@router.post("/route", response_model=NavigationResponse)
async def get_route(request: NavigationRequest):
    """
    Get an intelligent route between two points, considering crowd density,
    accessibility needs, and weather. Returns alternatives with reasoning.
    """
    try:
        agent_req = AgentRequest(
            agent_type=AgentType.NAVIGATION,
            payload={
                "origin": {
                    "lat": request.origin.lat,
                    "lng": request.origin.lng,
                    "label": request.origin.label,
                },
                "destination": {
                    "lat": request.destination.lat,
                    "lng": request.destination.lng,
                    "label": request.destination.label,
                },
                "accessibility_needs": [n.value if hasattr(n, "value") else str(n) for n in request.accessibility_needs],
                "avoid_crowds": request.avoid_crowds,
                "prefer_covered": request.prefer_covered,
                "language": request.language,
            },
        )

        result = await navigation_agent.execute(agent_req)
        data = result.result

        if "error" in data:
            return NavigationResponse(
                success=False,
                primary_route=None,  # type: ignore
                alternatives=[],
                crowd_warnings=[data["error"]],
                accessibility_notes=[],
                estimated_arrival=None,  # type: ignore
            )

        primary = _build_route(data.get("primary_route", {}))
        alternatives = [_build_route(a) for a in data.get("alternatives", [])]

        from datetime import datetime, timedelta
        eta = datetime.utcnow() + timedelta(
            seconds=primary.total_time_sec if primary else 0
        )

        return NavigationResponse(
            success=True,
            primary_route=primary,
            alternatives=alternatives,
            crowd_warnings=data.get("crowd_warnings", []),
            accessibility_notes=data.get("accessibility_notes", []),
            estimated_arrival=eta,
        )
    except Exception as e:
        return NavigationResponse(
            success=False,
            primary_route=None,  # type: ignore
            alternatives=[],
            crowd_warnings=[f"Navigation service unavailable: {str(e)}"],
            accessibility_notes=[],
            estimated_arrival=None,  # type: ignore
        )


def _build_route(raw: dict) -> Route:
    """Convert raw agent output into a Route schema."""
    if not raw:
        return None  # type: ignore

    waypoints = []
    for i, instr in enumerate(raw.get("instructions", [])):
        wp = RoutePoint(
            location=Location(lat=0, lng=0, label=raw.get("via_gate_name", "")),
            instruction=instr,
            distance_m=raw.get("total_distance_m", 0) / max(len(raw.get("instructions", [1])), 1),
            estimated_time_sec=int(raw.get("estimated_time_sec", 0) / max(len(raw.get("instructions", [1])), 1)),
            accessibility_notes="Accessible" if raw.get("accessible") else None,
        )
        waypoints.append(wp)

    return Route(
        id=str(uuid.uuid4()),
        origin=Location(
            lat=raw.get("origin", {}).get("lat", 0),
            lng=raw.get("origin", {}).get("lng", 0),
            label=raw.get("origin", {}).get("label"),
        ),
        destination=Location(
            lat=raw.get("destination", {}).get("lat", 0),
            lng=raw.get("destination", {}).get("lng", 0),
            label=raw.get("destination", {}).get("label"),
        ),
        waypoints=waypoints,
        total_distance_m=raw.get("total_distance_m", 0),
        total_time_sec=raw.get("estimated_time_sec", 0),
        crowd_factor=raw.get("crowd_density", 0),
        accessibility_score=1.0 if raw.get("accessible") else 0.5,
        alternative_routes=[],
        reasoning=raw.get("reason", raw.get("via_gate_name", "")),
    )