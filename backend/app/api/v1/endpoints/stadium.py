"""Stadium static + auxiliary data endpoints: map, gates, weather, transit, sustainability."""
from typing import Optional
import random

from fastapi import APIRouter

from app.models.schemas import (
    StadiumMap,
    Gate,
    Section,
    Facility,
    Location,
    GateStatus,
    WeatherResponse,
    WeatherData,
    TransitResponse,
    TransitData,
    SustainabilityResponse,
    SustainabilityMetric,
    BaseResponse,
)
from app.simulators.stadium_simulator import get_simulator

router = APIRouter()


@router.get("/map", response_model=StadiumMap)
async def get_stadium_map():
    """Static stadium layout: gates, sections, facilities (self-hosted GeoJSON)."""
    sim = get_simulator()
    gates = []
    for gate_id, g in sim.gates.items():
        gates.append(Gate(
            id=gate_id,
            name=g.name,
            location=Location(lat=g.lat, lng=g.lng),
            status=GateStatus.OPEN if g.status == "open" else GateStatus.CLOSED,
            capacity=g.capacity,
            current_count=g.current_count,
            accessibility_features=g.accessibility_features,
        ))

    sections = []
    for sec_id, s in sim.sections.items():
        sections.append(Section(
            id=sec_id,
            name=s["name"],
            level=s["level"],
            capacity=s["capacity"],
            current_occupancy=s["current_occupancy"],
        ))

    facilities = [
        Facility(id="fac_food_1", name="Concourse Food Court A", type="food",
                 location=Location(lat=40.7128, lng=-74.0060), accessible=True),
        Facility(id="fac_first_aid", name="Central First Aid", type="first_aid",
                 location=Location(lat=40.7125, lng=-74.0057), accessible=True),
        Facility(id="fac_info", name="Information Desk", type="information",
                 location=Location(lat=40.7126, lng=-74.0059), accessible=True),
    ]

    return StadiumMap(
        stadium_id="fifa_wc_2026_stadium_1",
        name="FIFA World Cup 2026 Stadium",
        gates=gates,
        sections=sections,
        facilities=facilities,
    )


@router.get("/weather", response_model=WeatherResponse)
async def get_weather():
    sim = get_simulator()
    w = sim.get_weather()
    return WeatherResponse(weather=WeatherData(
        temperature_c=w.temperature_c,
        condition=w.condition.value,
        humidity=w.humidity,
        wind_speed_kmh=w.wind_speed_kmh,
        precipitation_mm=w.precipitation_mm,
        alert=w.alert,
    ))


@router.get("/transit", response_model=TransitResponse)
async def get_transit():
    sim = get_simulator()
    transit = [
        TransitData(
            line=t.line,
            station=t.station,
            delay_minutes=t.delay_minutes,
            status=t.status.value,
            next_arrival=t.next_arrival,
        )
        for t in sim.get_transit()
    ]
    return TransitResponse(transit=transit)


@router.get("/sustainability", response_model=SustainabilityResponse)
async def get_sustainability():
    """Stretch module: synthetic utility metrics + GenAI insights (clearly simulated)."""
    metrics = [
        SustainabilityMetric(name="Electricity", value=round(random.uniform(1.8, 2.4), 2), unit="MWh", status="normal"),
        SustainabilityMetric(name="Water", value=round(random.uniform(40, 70), 1), unit="m³/h", status="normal"),
        SustainabilityMetric(name="Food Waste", value=round(random.uniform(60, 140), 0), unit="kg/h",
                             status="flag" if random.random() > 0.5 else "normal"),
        SustainabilityMetric(name="CO₂", value=round(random.uniform(0.8, 1.5), 2), unit="t/h", status="normal"),
    ]
    insights = [
        "Food waste spike detected at Concourse Food Court A — recommend adjusting staffing/restock cadence. (simulated)",
        "Energy draw is within expected match-day envelope. (simulated)",
    ]
    return SustainabilityResponse(metrics=metrics, insights=insights)


@router.post("/simulate/event", response_model=BaseResponse)
async def trigger_simulator_event(event_type: str, gate_id: Optional[str] = None, multiplier: float = 1.0):
    """Inject a dynamic event into the simulator (e.g., gate closure, surge)."""
    sim = get_simulator()
    sim.trigger_event(event_type, affects_gate=gate_id, multiplier=multiplier)
    return BaseResponse(success=True)