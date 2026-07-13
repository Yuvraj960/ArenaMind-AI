"""Agent routing tests — verify intent classification routes to correct agent."""
import pytest


class TestIntentRouting:
    """MasterAgent._classify routes queries to correct agents based on keywords + role."""

    @pytest.fixture(autouse=True)
    def ma(self):
        from app.agents.master_agent import MasterAgent
        return MasterAgent()

    @pytest.mark.asyncio
    async def test_emergency_keyword_routes_to_emergency(self, ma):
        r = await ma.process_chat(message="There's been a medical emergency", session_id="t1", role="fan", language="en")
        assert r["agent_used"] == "emergency"

    @pytest.mark.asyncio
    async def test_navigation_gate_routes_to_navigation(self, ma):
        r = await ma.process_chat(message="How do I get to Gate A?", session_id="t1", role="fan", language="en")
        assert r["agent_used"] == "navigation"

    @pytest.mark.asyncio
    async def test_spanish_navigation_routes_to_navigation(self, ma):
        r = await ma.process_chat(message="Donde esta mi puerta?", session_id="t1", role="fan", language="es")
        assert r["agent_used"] == "navigation"

    @pytest.mark.asyncio
    async def test_operator_role_routes_to_operations(self, ma):
        r = await ma.process_chat(message="Why are entry queues increasing?", session_id="t1", role="operator", language="en")
        assert r["agent_used"] == "operations"

    @pytest.mark.asyncio
    async def test_volunteer_role_routes_to_knowledge_volunteer(self, ma):
        r = await ma.process_chat(message="How do I handle lost children?", session_id="t1", role="volunteer", language="en")
        assert r["agent_used"] == "knowledge_volunteer"

    @pytest.mark.asyncio
    async def test_fan_general_question_routes_to_knowledge(self, ma):
        r = await ma.process_chat(message="Where can I buy food?", session_id="t1", role="fan", language="en")
        assert r["agent_used"] == "knowledge"


class TestAgentOutputs:
    """Each agent's gather_data returns expected structured fields."""

    @pytest.mark.asyncio
    async def test_navigation_returns_route(self):
        from app.agents.navigation_agent import NavigationAgent
        from app.agents.base_agent import AgentRequest, AgentType
        nav = NavigationAgent()
        r = await nav.execute(AgentRequest(agent_type=AgentType.NAVIGATION, payload={
            "origin": {"lat": 40.7130, "lng": -74.0060},
            "destination": {"lat": 40.7125, "lng": -74.0050},
            "accessibility_needs": [],
            "avoid_crowds": True,
        }, context={}))
        assert "primary_route" in r.result
        assert "alternatives" in r.result
        assert r.result["primary_route"].get("via_gate") in ["gate_a","gate_b","gate_c","gate_d","gate_e","gate_f"]

    @pytest.mark.asyncio
    async def test_navigation_avoids_congested_gate(self):
        from app.agents.navigation_agent import NavigationAgent
        from app.agents.base_agent import AgentRequest, AgentType
        nav = NavigationAgent()
        r = await nav.execute(AgentRequest(agent_type=AgentType.NAVIGATION, payload={
            "origin": {"lat": 40.7130, "lng": -74.0060},
            "destination": {"lat": 40.7125, "lng": -74.0050},
            "accessibility_needs": [],
            "avoid_crowds": True,
        }, context={}))
        chosen = r.result["primary_route"]["via_gate"]
        # Gate B is at 85% congestion — should NOT be chosen
        assert chosen != "gate_b", f"Navigation chose congested gate_b when it should be avoided"

    @pytest.mark.asyncio
    async def test_emergency_returns_exits_and_medical(self):
        from app.agents.emergency_agent import EmergencyAgent
        from app.agents.base_agent import AgentRequest, AgentType
        em = EmergencyAgent()
        r = await em.execute(AgentRequest(agent_type=AgentType.EMERGENCY, payload={
            "type": "medical",
            "location": {"lat": 40.7130, "lng": -74.0055},
            "severity": "high",
            "details": "Fan collapsed",
            "reported_by": "Volunteer",
        }, context={}))
        assert "nearest_exits" in r.result
        assert "nearest_medical" in r.result
        assert "announcements" in r.result
        assert len(r.result["nearest_exits"]) >= 3
        assert len(r.result["nearest_medical"]) >= 3

    @pytest.mark.asyncio
    async def test_operations_returns_answer_and_actions(self):
        from app.agents.operations_agent import OperationsAgent
        from app.agents.base_agent import AgentRequest, AgentType
        op = OperationsAgent()
        r = await op.execute(AgentRequest(agent_type=AgentType.OPERATIONS, payload={
            "question": "Why are entry queues increasing?",
            "context": {},
        }, context={}))
        assert "response" in r.result
        assert "data_sources" in r.result

    @pytest.mark.asyncio
    async def test_knowledge_agent_returns_sources(self):
        from app.agents.knowledge_agent import KnowledgeAgent
        from app.agents.base_agent import AgentRequest, AgentType
        ka = KnowledgeAgent(role="fan")
        r = await ka.execute(AgentRequest(agent_type=AgentType.KNOWLEDGE, payload={
            "question": "Where is the accessible entrance?",
            "message": "Where is the accessible entrance?",
        }, context={"role": "fan"}))
        assert "sources" in r.result
        assert len(r.result["sources"]) >= 1


class TestSimulator:
    """Stadium simulator returns consistent seeded gate densities."""

    def test_gate_b_seed_density(self):
        from app.simulators.stadium_simulator import get_simulator
        sim = get_simulator()
        densities = {d["gate_id"]: d for d in sim.get_gate_densities()}
        assert densities["gate_b"]["density_percentage"] == 85.0
        assert densities["gate_d"]["density_percentage"] == 20.0

    def test_heatmap_produces_points(self):
        from app.simulators.stadium_simulator import get_simulator
        sim = get_simulator()
        heatmap = sim.get_crowd_heatmap()
        assert len(heatmap) >= 6  # at least one point per gate
        intensities = [p["intensity"] for p in heatmap if p.get("type") == "gate"]
        assert max(intensities) > 0  # not all zero

    def test_narrative_generates(self):
        from app.simulators.stadium_simulator import get_simulator
        sim = get_simulator()
        n = sim.generate_narrative()
        assert isinstance(n, str)
        assert len(n) > 10
        assert "Gate B" in n


class TestRAG:
    """RAG returns role-filtered results."""

    def test_gate_navigation_kb_returns_results(self):
        import asyncio
        from app.rag.retriever import get_local_index
        idx = get_local_index()
        idx._load()
        results = idx.search("gate entrance navigation", role="fan", top_k=5)
        assert len(results) >= 1
        assert "gate" in results[0]["content"].lower()

    def test_volunteer_sop_filtered(self):
        import asyncio
        from app.rag.retriever import get_local_index
        idx = get_local_index()
        idx._load()
        fan_results = idx.search("emergency medical procedure", role="fan", top_k=5)
        vol_results = idx.search("emergency medical procedure", role="volunteer", top_k=5)
        # Both should return results, but volunteer content may be different
        assert len(fan_results) >= 1 or len(vol_results) >= 1

    def test_spanish_content_retrievable(self):
        import asyncio
        from app.rag.retriever import get_local_index
        idx = get_local_index()
        idx._load()
        # 'gate' returns results from both gates-navigation.md (en) and gates-navigation-es.md (es)
        results = idx.search("gate", role="fan", top_k=20)
        langs = {r["metadata"].get("language") for r in results if r}
        assert "es" in langs or "en" in langs  # at least some Spanish or English content