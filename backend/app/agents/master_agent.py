"""Master agent: intent classification → appropriate sub-agent → synthesized response.
No tool-call loop — sub-agents return structured data, master-agent LLM narrates."""
from typing import Dict, Any, Optional

from app.agents.base_agent import AgentRequest, AgentResponse
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.navigation_agent import NavigationAgent
from app.agents.crowd_agent import CrowdAgent
from app.agents.operations_agent import OperationsAgent
from app.agents.emergency_agent import EmergencyAgent
from app.models.schemas import AgentType


_MASTER_SYSTEM = """You are the ArenaMind master orchestrator for FIFA World Cup 2026.
Route the user's request to the appropriate specialist, then write a polished, complete answer
that incorporates the specialist's findings. Be specific, helpful, and calm — especially for
operations and emergency queries. Respond in the user's language."""


class MasterAgent:
    _agents = None

    @classmethod
    def _get_agents(cls):
        if cls._agents is None:
            cls._agents = {
                AgentType.KNOWLEDGE: KnowledgeAgent(role="fan"),
                AgentType.KNOWLEDGE_VOLUNTEER: KnowledgeAgent(role="volunteer"),
                AgentType.NAVIGATION: NavigationAgent(),
                AgentType.CROWD: CrowdAgent(),
                AgentType.OPERATIONS: OperationsAgent(),
                AgentType.EMERGENCY: EmergencyAgent(),
            }
        return cls._agents

    async def process_chat(
        self,
        message: str,
        session_id: str,
        role: str,
        language: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        context = context or {}
        context["role"] = role
        context["language"] = language
        context["session_id"] = session_id

        agent_type = self._classify(message, role)
        agents = self._get_agents()
        agent = agents.get(agent_type)
        if agent is None:
            agent = agents[AgentType.KNOWLEDGE]

        req = AgentRequest(agent_type=agent_type, payload={"message": message, "question": message}, context=context)
        resp = await agent.execute(req)

        return {
            "response": resp.result.get("response", str(resp.result)),
            "agent_used": agent_type.value,
            "confidence": resp.confidence,
            "sources": resp.result.get("sources", []),
            "suggested_actions": resp.result.get("suggested_actions", []),
            "routing": {"agent": agent_type.value, "llm_mode": resp.result.get("llm_mode", "live")},
        }

    def _classify(self, message: str, role: str) -> AgentType:
        lowered = message.lower()
        if any(k in lowered for k in ["emergency", "medical", "fire", "evacuate", "injury", "suspicious", "stampede", "collapsed"]):
            return AgentType.EMERGENCY
        if any(k in lowered for k in ["navigate", "route", "gate", "how do i get", "cómo llego", "dónde está", "donde esta", "directions", "entrance", "puerta"]):
            return AgentType.NAVIGATION
        if role in ("operator", "emergency") or any(k in lowered for k in ["staff", "queue", "why is", "operation", "transit delay"]):
            return AgentType.OPERATIONS
        if any(k in lowered for k in ["crowd", "congestion", "density", "heatmap", "predict"]):
            return AgentType.CROWD
        if role == "volunteer":
            return AgentType.KNOWLEDGE_VOLUNTEER
        return AgentType.KNOWLEDGE


_master: Optional[MasterAgent] = None


def get_master_agent() -> MasterAgent:
    global _master
    if _master is None:
        _master = MasterAgent()
    return _master