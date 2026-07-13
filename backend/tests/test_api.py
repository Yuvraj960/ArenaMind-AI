"""API layer smoke tests — health, crowd gates, navigation, chat, emergency."""
import pytest


class TestHealthAndRoot:
    def test_root_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "ArenaMind" in r.text

    def test_health_returns_200(self, client):
        # health is at the root of api_router (/api/v1/)
        r = client.get("/api/v1/")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True

    def test_crowd_gates_returns_200(self, client):
        r = client.get("/api/v1/crowd/gates")
        assert r.status_code == 200
        gates = r.json()
        assert len(gates) == 6
        densities = {g["gate_id"]: g["density_percentage"] for g in gates}
        assert 80 <= densities["gate_b"] <= 90  # seeded ~85%
        assert densities["gate_d"] < 30  # seeded ~20%


class TestNavigationEndpoint:
    def test_navigation_returns_route(self, client):
        r = client.post("/api/v1/navigation/route", json={
            "origin": {"lat": 40.7130, "lng": -74.0060},
            "destination": {"lat": 40.7125, "lng": -74.0050},
            "accessibility_needs": [],
            "avoid_crowds": True,
        })
        assert r.status_code == 200
        data = r.json()
        assert "primary_route" in data
        # primary_route has id, reasoning, waypoints, etc.
        assert data["primary_route"]["reasoning"] is not None

    def test_navigation_avoids_congested_gate_b(self, client):
        # With avoid_crowds=True Gate B at 85% should NOT be chosen
        r = client.post("/api/v1/navigation/route", json={
            "origin": {"lat": 40.7130, "lng": -74.0060},
            "destination": {"lat": 40.7125, "lng": -74.0050},
            "accessibility_needs": [],
            "avoid_crowds": True,
        })
        data = r.json()
        reasoning = data["primary_route"]["reasoning"]
        # Gate C or D (low density) should be chosen, Gate B (85%) should not be in reasoning
        assert "gate_b" not in reasoning.lower() or data.get("crowd_warnings"), \
            "Navigation chose congested gate_b despite avoid_crowds=True"


class TestChatEndpoint:
    def test_chat_fan_returns_response(self, client):
        r = client.post("/api/v1/chat", json={
            "message": "Where is the accessible entrance?",
            "language": "en",
            "role": "fan",
            "session_id": "test-s1",
        })
        assert r.status_code == 200
        data = r.json()
        assert "response" in data
        assert data["agent_used"] in ["knowledge", "navigation"]

    def test_chat_emergency_routes_to_emergency(self, client):
        r = client.post("/api/v1/chat", json={
            "message": "Someone collapsed near section 103",
            "language": "en",
            "role": "fan",
            "session_id": "test-s2",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["agent_used"] == "emergency"

    def test_chat_spanish_routes_to_navigation(self, client):
        r = client.post("/api/v1/chat", json={
            "message": "Donde esta la puerta de entrada?",
            "language": "es",
            "role": "fan",
            "session_id": "test-s3",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["agent_used"] == "navigation"


class TestEmergencyEndpoint:
    def test_emergency_medical_returns_exits_and_announcements(self, client):
        r = client.post("/api/v1/emergency/respond", json={
            "type": "medical",
            "location": {"lat": 40.7130, "lng": -74.0055},
            "severity": "high",
            "details": "Fan collapsed",
            "reported_by": "Volunteer",
        })
        assert r.status_code == 200
        data = r.json()
        assert "nearest_exits" in data
        assert "nearest_medical" in data
        assert "announcements" in data
        assert len(data["nearest_exits"]) >= 3
        assert len(data["nearest_medical"]) >= 3
        # Announcements is a list of {"language": "...", "text": "..."} dicts
        assert len(data["announcements"]) >= 2
        langs = {a["language"] for a in data["announcements"] if isinstance(a, dict)}
        assert "en" in langs


class TestOperationsEndpoint:
    def test_operations_query_returns_answer_and_sources(self, client):
        r = client.post("/api/v1/operations/query", json={
            "question": "Why are entry queues increasing?",
        })
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data  # operations returns 'answer'
        assert "data_sources" in data
        assert len(data["data_sources"]) >= 1

    def test_crowd_heatmap_returns_points(self, client):
        r = client.get("/api/v1/crowd/heatmap")
        assert r.status_code == 200
        resp = r.json()
        # Response is BaseResponse + 'heatmap' field
        assert "heatmap" in resp
        points = resp["heatmap"]
        assert len(points) >= 6
        # All points should have intensity and location fields
        assert all("intensity" in p for p in points)
        assert all("lat" in p and "lng" in p for p in points)


class TestStadiumSimulatorEventTrigger:
    def test_trigger_surge_event_changes_gate_density(self, client):
        # Get baseline density
        r1 = client.get("/api/v1/crowd/gates")
        gates_before = {g["gate_id"]: g["density_percentage"] for g in r1.json()}
        initial = gates_before["gate_b"]

        # Trigger surge — simulation endpoint accepts query params
        r2 = client.post(
            "/api/v1/stadium/simulate/event",
            params={"event_type": "surge", "gate_id": "gate_b", "multiplier": 3.0},
        )
        assert r2.status_code == 200

        # Read updated density
        r3 = client.get("/api/v1/crowd/gates")
        gates_after = {g["gate_id"]: g["density_percentage"] for g in r3.json()}
        assert gates_after["gate_b"] >= initial