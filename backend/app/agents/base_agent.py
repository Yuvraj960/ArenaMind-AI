"""Base agent. Agents gather their own real data (simulator/RAG), then ask the LLM
exactly once to narrate. No LLM-driven tool-call loop — reliable online and offline."""
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from app.core.llm_client import LLMClient, LLMMessage, get_llm_client
from app.models.schemas import AgentType, AgentRequest, AgentResponse


class BaseAgent(ABC):
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.llm_client: LLMClient = get_llm_client()

    @abstractmethod
    def get_system_prompt(self) -> str:
        ...

    @abstractmethod
    async def gather_data(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Return a dict containing:
          - 'context_text': str — gathered facts shown to the LLM
          - 'tools_used': list[str] — names of real tools called
          - any other passthrough keys that go straight into the AgentResponse.result
        """
        ...

    def format_user_message(self, payload: Dict[str, Any], context_text: str) -> str:
        return f"Request: {payload}\n\nGathered context:\n{context_text}"

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start = time.time()
        data = await self.gather_data(request.payload, request.context)
        context_text = data.pop("context_text", "")
        tools_used = data.pop("tools_used", [])
        structured = data  # remaining keys are passthrough

        messages = [
            LLMMessage(role="system", content=self.get_system_prompt()),
            LLMMessage(role="user", content=self.format_user_message(request.payload, context_text)),
        ]

        try:
            resp = await self.llm_client.chat(messages)
            content = resp.content
            llm_mode = resp.mode
        except Exception as e:
            content = self._fallback(context_text, str(e))
            llm_mode = "fallback"

        structured["response"] = content
        structured["llm_mode"] = llm_mode
        structured.setdefault("sources", [])
        structured.setdefault("suggested_actions", [])

        return AgentResponse(
            agent_type=self.agent_type,
            result=structured,
            confidence=0.9,
            tools_used=tools_used,
            execution_time_ms=int((time.time() - start) * 1000),
        )

    def _fallback(self, context_text: str, err: str) -> str:
        base = context_text or "No live data available."
        return f"(Live AI temporarily unavailable — {err}. Showing gathered data.) {base}"
