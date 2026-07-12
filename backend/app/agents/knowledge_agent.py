from typing import Dict, Any, List

from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentType
from app.rag.retriever import get_knowledge_retriever


class KnowledgeAgent(BaseAgent):
    """Shared RAG agent for fans (Matchday Assistant) and volunteers (Volunteer Copilot).
    Same collection, different system prompt + role scoping — never duplicate RAG."""

    def __init__(self, role: str = "fan"):
        super().__init__(AgentType.KNOWLEDGE)
        self.role = role

    def get_system_prompt(self) -> str:
        if self.role == "volunteer":
            return (
                "You are the ArenaMind Volunteer Copilot for FIFA World Cup 2026. Answer questions "
                "from volunteers about emergency procedures, lost & found, medical response, accessibility "
                "assistance, security escalation, and stadium policy. Be authoritative but supportive. "
                "Reference specific SOPs and resources from the gathered context. If the user writes in "
                "another language, reply in that language."
            )
        return (
            "You are the ArenaMind Matchday Assistant for FIFA World Cup 2026 fans. Answer questions "
            "about navigation, gates, amenities, food, merchandise, tickets, transport, accessibility, and "
            "stadium info. Be helpful, friendly, and concise. Give specific gate names, walking times, and "
            "nearby facilities from the gathered context. If the fan writes in another language, reply in "
            "that language."
        )

    async def gather_data(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        question = payload.get("question") or payload.get("message") or ""
        role = context.get("role", self.role)
        retriever = await get_knowledge_retriever()
        docs = await retriever.search(question, role=role, top_k=5)

        context_text = "\n---\n".join(
            f"[{d['metadata'].get('source','?')}] {d['content']}" for d in docs
        ) or "No documents retrieved."

        sources = [
            {"content": d["content"][:400], "score": d["score"], "metadata": d["metadata"]}
            for d in docs
        ]
        return {
            "context_text": context_text,
            "sources": sources,
            "suggested_actions": self._suggest(question),
            "tools_used": ["search_knowledge"],
        }

    def _suggest(self, question: str) -> List[str]:
        q = question.lower()
        if any(k in q for k in ["gate", "puerta", "entrance", "exit"]):
            return ["Tap Navigate for a live route", "Check crowd heatmap"]
        if "food" in q or "eat" in q:
            return ["Show nearest food", "View map"]
        if "bath" in q or "restroom" in q or "baño" in q:
            return ["Show nearest restroom", "View map"]
        return ["Ask for directions", "View crowd heatmap"]
