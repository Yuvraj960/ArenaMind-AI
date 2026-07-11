"""Pydantic schemas for ArenaMind AI — the single source of truth for API contracts.

These mirror API_CONTRACTS.md. Frontend and backend must never drift from these.
"""
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    FAN = "fan"
    VOLUNTEER = "volunteer"
    OPERATOR = "operator"
    EMERGENCY = "emergency"
    ADMIN = "admin"


class GateStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    RESTRICTED = "restricted"
    EMERGENCY_ONLY = "emergency_only"


class AccessibilityNeed(str, Enum):
    WHEELCHAIR = "wheelchair"
    AVOID_STAIRS = "avoid_stairs"
    LOW_MOBILITY = "low_mobility"
    VISUAL_IMPAIRMENT = "visual_impairment"
    HEARING_IMPAIRMENT = "hearing_impairment"
    NONE = "none"


class AgentType(str, Enum):
    MASTER = "master"
    NAVIGATION = "navigation"
    CROWD = "crowd"
    OPERATIONS = "operations"
    EMERGENCY = "emergency"
    TRANSLATION = "translation"
    KNOWLEDGE = "knowledge"
    KNOWLEDGE_VOLUNTEER = "knowledge_volunteer"
    WEATHER = "weather"
    TRANSIT = "transit"


# ---------------------------------------------------------------------------
# Base responses
# ---------------------------------------------------------------------------

class BaseResponse(BaseModel):
    success: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseResponse):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Locations & routes
# ---------------------------------------------------------------------------

class Location(BaseModel):
    lat: float
    lng: float
    level: int = 0
    label: Optional[str] = None


class RoutePoint(BaseModel):
    location: Location
    instruction: str
    distance_m: float
    estimated_time_sec: int
    accessibility_notes: Optional[str] = None


class Route(BaseModel):
    id: str
    origin: Location
    destination: Location
    waypoints: List[RoutePoint] = []
    total_distance_m: float
    total_time_sec: int
    crowd_factor: float = 0.0
    accessibility_score: float = 1.0
    alternative_routes: List["Route"] = []
    reasoning: str = ""


class NavigationRequest(BaseModel):
    origin: Location
    destination: Location
    accessibility_needs: List[str] = Field(default_factory=list)
    avoid_crowds: bool = True
    prefer_covered: bool = False
    audience: str = "fan"
    language: str = "en"


class NavigationResponse(BaseResponse):
    primary_route: Optional[Route] = None
    alternatives: List[Route] = []
    crowd_warnings: List[str] = []
    accessibility_notes: List[str] = []
    estimated_arrival: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Crowd
# ---------------------------------------------------------------------------

class CrowdDensity(BaseModel):
    gate_id: str
    gate_name: str
    current_count: int
    capacity: int
    density_percentage: float
    trend: Literal["increasing", "stable", "decreasing"]
    estimated_wait_minutes: int
    status: str = "open"
    accessibility_features: List[str] = []


class CrowdHeatmapPoint(BaseModel):
    lat: float
    lng: float
    intensity: float  # 0-1
    count: int
    type: str = "gate"
    gate_id: Optional[str] = None
    section_id: Optional[str] = None


class CrowdHeatmapResponse(BaseResponse):
    stadium_id: str
    heatmap: List[CrowdHeatmapPoint]
    gates: List[CrowdDensity]
    narrative: str
    overall_status: str = "normal"


class CrowdPrediction(BaseModel):
    gate_id: str
    current_density: float
    predicted_density: float
    trend: str
    risk_level: Literal["low", "medium", "high"]
    recommended_action: str


class CrowdPredictionsResponse(BaseResponse):
    predictions: List[CrowdPrediction]
    horizon_minutes: int


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

class OperationsQuery(BaseModel):
    question: str
    context: Dict[str, Any] = {}
    role: UserRole = UserRole.OPERATOR


class OperationsResponse(BaseResponse):
    answer: str
    data_sources: List[str] = []
    confidence: float = 0.8
    recommended_actions: List[str] = []
    related_metrics: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Emergency
# ---------------------------------------------------------------------------

class EmergencyScenario(BaseModel):
    type: Literal["medical", "fire", "suspicious_object", "overcrowding", "weather", "stampede", "security"]
    location: Location
    severity: Literal["low", "medium", "high", "critical"]
    details: str
    reported_by: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmergencyResource(BaseModel):
    id: str
    name: str
    type: str
    lat: float
    lng: float
    distance_m: int
    estimated_time_sec: int
    accessible: bool = True
    capacity: Optional[int] = None


class EmergencyResponse(BaseResponse):
    scenario_id: str
    scenario_type: str
    severity: str
    immediate_actions: List[str]
    evacuation_routes: List[Dict[str, Any]]
    nearest_exits: List[Dict[str, Any]]
    nearest_medical: List[Dict[str, Any]]
    nearest_security: List[Dict[str, Any]]
    assigned_staff: List[Dict[str, Any]]
    announcements: List[Dict[str, str]]
    estimated_clearance_time_min: int
    coordination_notes: str


# ---------------------------------------------------------------------------
# Knowledge / RAG
# ---------------------------------------------------------------------------

class KnowledgeDoc(BaseModel):
    id: str
    title: str
    content: str
    category: str
    tags: List[str] = []
    language: str = "en"
    metadata: Dict[str, Any] = {}


class KnowledgeSearchResult(BaseModel):
    content: str
    score: float = 1.0
    metadata: Dict[str, Any] = {}


class KnowledgeSearchResults(BaseResponse):
    results: List[KnowledgeSearchResult]
    query: str


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    language: str = "en"
    metadata: Dict[str, Any] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language: str = "en"
    role: UserRole = UserRole.FAN
    audience: str = "fan"
    context: Dict[str, Any] = {}


class ChatResponse(BaseResponse):
    response: str
    session_id: str
    language: str
    sources: List[KnowledgeSearchResult] = []
    suggested_actions: List[str] = []
    agent_used: Optional[str] = None


# ---------------------------------------------------------------------------
# Agent orchestrator
# ---------------------------------------------------------------------------

class AgentRequest(BaseModel):
    agent_type: AgentType
    payload: Dict[str, Any]
    context: Dict[str, Any] = {}
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    agent_type: AgentType
    result: Dict[str, Any]
    confidence: float
    tools_used: List[str] = []
    execution_time_ms: int


# ---------------------------------------------------------------------------
# Stadium static data
# ---------------------------------------------------------------------------

class Gate(BaseModel):
    id: str
    name: str
    location: Location
    status: GateStatus = GateStatus.OPEN
    capacity: int
    current_count: int = 0
    accessibility_features: List[str] = []


class Section(BaseModel):
    id: str
    name: str
    level: int
    capacity: int
    current_occupancy: int = 0
    accessible: bool = True


class Facility(BaseModel):
    id: str
    name: str
    type: Literal["restroom", "food", "merchandise", "first_aid", "information", "accessibility", "prayer_room", "family_room"]
    location: Location
    accessible: bool = True
    operating_hours: Optional[str] = None


class StadiumMap(BaseResponse):
    stadium_id: str
    name: str
    gates: List[Gate]
    sections: List[Section]
    facilities: List[Facility]


# ---------------------------------------------------------------------------
# Weather, transit, sustainability
# ---------------------------------------------------------------------------

class WeatherData(BaseModel):
    temperature_c: float
    condition: Literal["clear", "cloudy", "rain", "storm", "extreme_heat"]
    humidity: float
    wind_speed_kmh: float
    precipitation_mm: float
    alert: Optional[str] = None


class TransitData(BaseModel):
    line: str
    station: str
    delay_minutes: int
    status: Literal["on_time", "delayed", "cancelled", "crowded"]
    next_arrival: Optional[datetime] = None


class TransitResponse(BaseResponse):
    transit: List[TransitData]


class WeatherResponse(BaseResponse):
    weather: WeatherData


class SustainabilityMetric(BaseModel):
    name: str
    value: float
    unit: str
    status: str = "normal"


class SustainabilityResponse(BaseResponse):
    metrics: List[SustainabilityMetric]
    insights: List[str]


# ---------------------------------------------------------------------------
# Simulators
# ---------------------------------------------------------------------------

class SimulatorConfig(BaseModel):
    crowd_base_multiplier: float = 1.0
    weather_impact: float = 1.0
    transit_delay_factor: float = 1.0
    enable_dynamic_events: bool = True


class SimulatorEventRequest(BaseModel):
    event_type: str
    gate_id: Optional[str] = None
    multiplier: float = 1.0