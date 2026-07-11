import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field


class WeatherCondition(str, Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    EXTREME_HEAT = "extreme_heat"


class TransitStatus(str, Enum):
    ON_TIME = "on_time"
    DELAYED = "delayed"
    CANCELLED = "cancelled"
    CROWDED = "crowded"


@dataclass
class GateState:
    gate_id: str
    name: str
    lat: float
    lng: float
    capacity: int
    accessibility_features: List[str] = field(default_factory=list)
    current_count: int = 0
    status: str = "open"
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class CrowdSnapshot:
    gate_id: str
    section_id: Optional[str]
    density: float
    count: int
    capacity: int
    trend: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WeatherData:
    temperature_c: float
    condition: WeatherCondition
    humidity: float
    wind_speed_kmh: float
    precipitation_mm: float
    alert: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TransitData:
    line: str
    station: str
    delay_minutes: int
    status: TransitStatus
    next_arrival: datetime
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SimulatorConfig:
    crowd_base_multiplier: float = 1.0
    weather_impact: float = 1.0
    transit_delay_factor: float = 1.0
    enable_dynamic_events: bool = True


class StadiumSimulator:
    def __init__(self, config: Optional[SimulatorConfig] = None):
        self.config = config or SimulatorConfig()
        self.gates: Dict[str, GateState] = {}
        self.sections: Dict[str, Dict] = {}
        self.weather: WeatherData = WeatherData(22.0, WeatherCondition.CLEAR, 60.0, 10.0, 0.0)
        self.transit: List[TransitData] = []
        self._crowd_history: Dict[str, List[CrowdSnapshot]] = {}
        self._dynamic_events: List[Dict] = []
        self._running = False

        self._initialize_stadium()

    def _initialize_stadium(self):
        # Initialize gates with realistic FIFA WC stadium layout + baseline crowd
        # Gate B starts congested to make the navigation routing demo beat meaningful
        gates_data = [
            {"gate_id": "gate_a", "name": "Gate A - North Entrance", "lat": 40.7130, "lng": -74.0055, "capacity": 5000, "features": ["wheelchair", "express"], "seed_count": 1200},
            {"gate_id": "gate_b", "name": "Gate B - East Entrance", "lat": 40.7125, "lng": -74.0050, "capacity": 4000, "features": ["wheelchair"], "seed_count": 3400},  # ~85% — demo beat
            {"gate_id": "gate_c", "name": "Gate C - South Entrance", "lat": 40.7120, "lng": -74.0055, "capacity": 4500, "features": ["wheelchair", "express"], "seed_count": 900},
            {"gate_id": "gate_d", "name": "Gate D - West Entrance", "lat": 40.7125, "lng": -74.0060, "capacity": 3500, "features": ["wheelchair"], "seed_count": 700},
            {"gate_id": "gate_e", "name": "Gate E - VIP Entrance", "lat": 40.7128, "lng": -74.0058, "capacity": 2000, "features": ["priority", "assistance"], "seed_count": 400},
            {"gate_id": "gate_f", "name": "Gate F - Accessible Entrance", "lat": 40.7122, "lng": -74.0062, "capacity": 1500, "features": ["wheelchair", "priority", "assistance"], "seed_count": 300},
        ]

        for g in gates_data:
            self.gates[g["gate_id"]] = GateState(
                gate_id=g["gate_id"],
                name=g["name"],
                lat=g["lat"],
                lng=g["lng"],
                capacity=g["capacity"],
                accessibility_features=g["features"],
                current_count=g["seed_count"],
            )

        # Initialize sections
        for level in [1, 2, 3]:
            for side in ["north", "south", "east", "west"]:
                sec_id = f"section_{side}_{level}"
                self.sections[sec_id] = {
                    "id": sec_id,
                    "name": f"Section {side.title()} Level {level}",
                    "level": level,
                    "capacity": random.randint(2000, 5000),
                    "current_occupancy": 0,
                    "accessible": True,
                }

        # Initialize transit
        now = datetime.now()
        self.transit = [
            TransitData("Metro Line 1", "Stadium Central", 0, TransitStatus.ON_TIME, now + timedelta(minutes=3)),
            TransitData("Metro Line 2", "Stadium East", 5, TransitStatus.DELAYED, now + timedelta(minutes=8)),
            TransitData("Bus Route 101", "Stadium West", 0, TransitStatus.ON_TIME, now + timedelta(minutes=5)),
            TransitData("Bus Route 102", "Stadium North", 10, TransitStatus.CROWDED, now + timedelta(minutes=12)),
            TransitData("Train Line A", "Stadium Main", 0, TransitStatus.ON_TIME, now + timedelta(minutes=2)),
        ]

    async def start_simulation(self, interval_seconds: int = 5):
        """Start continuous simulation"""
        self._running = True
        while self._running:
            await self._update_crowd()
            await self._update_weather()
            await self._update_transit()
            await asyncio.sleep(interval_seconds)

    def stop_simulation(self):
        self._running = False

    async def _update_crowd(self):
        """Simulate crowd flow at gates"""
        now = datetime.now()
        hour = now.hour

        # Time-based flow patterns
        if 16 <= hour <= 18:
            base_multiplier = 1.5 * self.config.crowd_base_multiplier
        elif 21 <= hour <= 23:
            base_multiplier = 1.8 * self.config.crowd_base_multiplier
        elif 19 <= hour <= 21:
            base_multiplier = 0.3 * self.config.crowd_base_multiplier
        else:
            base_multiplier = 0.1 * self.config.crowd_base_multiplier

        for gate_id, gate in self.gates.items():
            if gate.status != "open":
                continue

            flow_rate = base_multiplier * random.uniform(0.5, 1.5) * self.config.weather_impact

            # Weather impact
            if self.weather.condition == WeatherCondition.RAIN:
                flow_rate *= 0.7
            elif self.weather.condition == WeatherCondition.STORM:
                flow_rate *= 0.4

            # Transit impact
            transit_crowded = any(t.status == TransitStatus.CROWDED for t in self.transit)
            if transit_crowded:
                flow_rate *= 1.3

            # Dynamic events
            for event in self._dynamic_events:
                if event.get("affects_gate") == gate_id:
                    flow_rate *= event.get("multiplier", 1.0)

            delta = int(flow_rate * random.uniform(-0.2, 1.0))
            gate.current_count = max(0, min(gate.capacity, gate.current_count + delta))
            gate.last_update = now

            # Record snapshot
            snapshot = CrowdSnapshot(
                gate_id=gate_id,
                section_id=None,
                density=gate.current_count / gate.capacity if gate.capacity > 0 else 0,
                count=gate.current_count,
                capacity=gate.capacity,
                trend="increasing" if delta > 0 else "decreasing" if delta < 0 else "stable",
                timestamp=now,
            )

            if gate_id not in self._crowd_history:
                self._crowd_history[gate_id] = []
            self._crowd_history[gate_id].append(snapshot)
            if len(self._crowd_history[gate_id]) > 100:
                self._crowd_history[gate_id] = self._crowd_history[gate_id][-100:]

    async def _update_weather(self):
        """Simulate weather changes"""
        self.weather.temperature_c += random.uniform(-0.5, 0.5)
        self.weather.temperature_c = max(5, min(40, self.weather.temperature_c))

        if random.random() < 0.01:
            conditions = list(WeatherCondition)
            self.weather.condition = random.choice(conditions)

            if self.weather.condition == WeatherCondition.RAIN:
                self.weather.precipitation_mm = random.uniform(1, 10)
                self.weather.alert = "Light rain expected"
            elif self.weather.condition == WeatherCondition.STORM:
                self.weather.precipitation_mm = random.uniform(10, 50)
                self.weather.wind_speed_kmh = random.uniform(50, 80)
                self.weather.alert = "Storm warning - seek covered areas"
            elif self.weather.condition == WeatherCondition.EXTREME_HEAT:
                self.weather.temperature_c = random.uniform(35, 42)
                self.weather.alert = "Extreme heat warning - stay hydrated"
            else:
                self.weather.precipitation_mm = 0
                self.weather.alert = None

        self.weather.timestamp = datetime.now()

    async def _update_transit(self):
        """Simulate transit updates"""
        for t in self.transit:
            if random.random() < 0.1:
                t.delay_minutes = random.randint(0, 20) * self.config.transit_delay_factor
                if t.delay_minutes > 15:
                    t.status = TransitStatus.DELAYED
                elif t.delay_minutes > 0:
                    t.status = TransitStatus.CROWDED
                else:
                    t.status = TransitStatus.ON_TIME

            t.next_arrival = datetime.now() + timedelta(minutes=random.randint(2, 15))
            t.timestamp = datetime.now()

    def get_crowd_heatmap(self) -> List[Dict[str, Any]]:
        """Generate heatmap data for visualization"""
        heatmap = []

        for gate_id, gate in self.gates.items():
            density = gate.current_count / gate.capacity if gate.capacity > 0 else 0
            heatmap.append({
                "lat": gate.lat + random.uniform(-0.0005, 0.0005),
                "lng": gate.lng + random.uniform(-0.0005, 0.0005),
                "intensity": min(1.0, density * 1.5),
                "count": gate.current_count,
                "type": "gate",
                "gate_id": gate_id,
            })

        for sec_id, section in self.sections.items():
            occupancy = section["current_occupancy"] / section["capacity"] if section["capacity"] > 0 else 0
            lat_offset = {"north": 0.001, "south": -0.001, "east": 0, "west": 0}
            lng_offset = {"north": 0, "south": 0, "east": 0.001, "west": -0.001}

            for side in ["north", "south", "east", "west"]:
                if side in sec_id:
                    heatmap.append({
                        "lat": 40.7128 + lat_offset[side] + random.uniform(-0.0003, 0.0003),
                        "lng": -74.0060 + lng_offset[side] + random.uniform(-0.0003, 0.0003),
                        "intensity": min(1.0, occupancy),
                        "count": section["current_occupancy"],
                        "type": "section",
                        "section_id": sec_id,
                    })

        return heatmap

    def get_gate_densities(self) -> List[Dict[str, Any]]:
        """Get current gate densities for API"""
        densities = []
        for gate_id, gate in self.gates.items():
            density = gate.current_count / gate.capacity if gate.capacity > 0 else 0
            densities.append({
                "gate_id": gate_id,
                "gate_name": gate.name,
                "current_count": gate.current_count,
                "capacity": gate.capacity,
                "density_percentage": round(density * 100, 1),
                "trend": self._get_trend(gate_id),
                "estimated_wait_minutes": self._estimate_wait(gate),
                "status": gate.status,
                "accessibility_features": gate.accessibility_features,
            })
        return densities

    def _get_trend(self, gate_id: str) -> str:
        history = self._crowd_history.get(gate_id, [])
        if len(history) < 2:
            return "stable"
        recent = history[-5:]
        avg_recent = sum(s.count for s in recent) / len(recent)
        avg_older = sum(s.count for s in history[-10:-5]) / 5 if len(history) >= 10 else avg_recent

        if avg_recent > avg_older * 1.1:
            return "increasing"
        elif avg_recent < avg_older * 0.9:
            return "decreasing"
        return "stable"

    def _estimate_wait(self, gate: GateState) -> int:
        if gate.current_count == 0:
            return 0
        density = gate.current_count / gate.capacity
        base_wait = density * 30
        return int(base_wait * self.config.weather_impact)

    def get_weather(self) -> WeatherData:
        return self.weather

    def get_transit(self) -> List[TransitData]:
        return self.transit

    def trigger_event(self, event_type: str, **kwargs):
        """Trigger a dynamic event"""
        event = {
            "type": event_type,
            "timestamp": datetime.now(),
            **kwargs,
        }
        self._dynamic_events.append(event)
        asyncio.create_task(self._expire_event(event, 30 * 60))

    async def _expire_event(self, event: Dict, delay_seconds: int):
        await asyncio.sleep(delay_seconds)
        if event in self._dynamic_events:
            self._dynamic_events.remove(event)

    def generate_narrative(self) -> str:
        """Generate GenAI-style crowd narrative"""
        densities = self.get_gate_densities()
        high_density = [d for d in densities if d["density_percentage"] > 70]
        increasing = [d for d in densities if d["trend"] == "increasing"]

        if not high_density and not increasing:
            return "Crowd levels are normal across all gates. No congestion detected."

        parts = []

        if high_density:
            gates_str = ", ".join([g["gate_name"] for g in high_density[:3]])
            parts.append(f"High density detected at {gates_str}.")

        if increasing:
            gates_str = ", ".join([g["gate_name"] for g in increasing[:3]])
            parts.append(f"Crowd buildup trending at {gates_str}.")

        if self.weather.condition in [WeatherCondition.RAIN, WeatherCondition.STORM]:
            parts.append(f"Weather impact: {self.weather.condition.value} reducing entry flow by ~30%.")

        delayed = [t for t in self.transit if t.status in [TransitStatus.DELAYED, TransitStatus.CROWDED]]
        if delayed:
            lines = ", ".join([t.line for t in delayed[:2]])
            parts.append(f"Transit delays on {lines} may cause arrival surges.")

        return " ".join(parts)


# Global simulator instance
_simulator: Optional[StadiumSimulator] = None


def get_simulator() -> StadiumSimulator:
    global _simulator
    if _simulator is None:
        _simulator = StadiumSimulator()
    return _simulator


async def start_simulator():
    simulator = get_simulator()
    await simulator.start_simulation()


def stop_simulator():
    simulator = get_simulator()
    simulator.stop_simulation()