"""Provider-agnostic LLM client with graceful degradation.

Selection order:
  1. Anthropic if ANTHROPIC_API_KEY set
  2. OpenAI if OPENAI_API_KEY set
  3. MockLLMClient (deterministic, scenario-aware) — clearly flagged via `mode="mock"`

Agents gather their own tool data and call the LLM exactly once for the final narrative,
so the mock stays coherent even with no API key.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, AsyncGenerator
from pydantic import BaseModel
import json

from app.core.config import get_settings


class LLMMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMResponse(BaseModel):
    content: str
    model: Optional[str] = None
    usage: Optional[dict] = None
    tool_calls: Optional[List[dict]] = None
    mode: str = "live"  # "live" | "mock" | "fallback"


class LLMClient(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        ...


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------

class AnthropicClient(LLMClient):
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=self.settings.ANTHROPIC_API_KEY)
        except Exception as e:  # pragma: no cover - env-dependent
            print(f"[llm] Anthropic init failed: {e}")

    async def chat(self, messages, temperature=0.3, max_tokens=2048) -> LLMResponse:
        system, convo = _split_system(messages)
        resp = await self.client.messages.create(
            model=self.settings.DEFAULT_LLM_MODEL,
            system=system or None,
            messages=convo,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        return LLMResponse(
            content=text,
            model=resp.model,
            usage={"input": resp.usage.input_tokens, "output": resp.usage.output_tokens},
            mode="live",
        )


# ---------------------------------------------------------------------------
# OpenAI (optional alternative provider)
# ---------------------------------------------------------------------------

class OpenAIClient(LLMClient):
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        except Exception as e:  # pragma: no cover
            print(f"[llm] OpenAI init failed: {e}")

    async def chat(self, messages, temperature=0.3, max_tokens=2048) -> LLMResponse:
        convo = [{"role": m.role, "content": m.content} for m in messages]
        resp = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=convo,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return LLMResponse(
            content=resp.choices[0].message.content or "",
            model=resp.model,
            usage={"input": resp.usage.prompt_tokens, "output": resp.usage.completion_tokens},
            mode="live",
        )


# ---------------------------------------------------------------------------
# Mock (no-key fallback) — deterministic, scenario + language aware
# ---------------------------------------------------------------------------

class MockLLMClient(LLMClient):
    """Used when no real LLM key is configured. Responses are clearly flagged
    `mode="mock"` so they're never silently presented as model output."""

    async def chat(self, messages, temperature=0.3, max_tokens=2048) -> LLMResponse:
        system = next((m.content for m in messages if m.role == "system"), "")
        user = next((m.content for m in messages if m.role == "user"), "")
        text = self._generate(system, user)
        return LLMResponse(content=text, model="mock", mode="mock")

    def _generate(self, system: str, user: str) -> str:
        lowered = (system + "\n" + user).lower()
        is_spanish = any(w in user.lower() for w in ["dónde", "puerta", "baño", "ayuda", "emergencia", "¿d", "ó"])

        # Grab any gathered context block the agent embedded in the user message
        ctx = _extract_block(user, "Gathered context")
        ctx_lines = [ln.strip() for ln in ctx.splitlines() if ln.strip()] if ctx else []

        if "emergency" in lowered or "evacuation" in lowered:
            return _mock_emergency(ctx_lines)
        if "navigation" in lowered or "route" in lowered and "gate" in lowered:
            return _mock_navigation(ctx_lines, is_spanish)
        if "operations copilot" in lowered or "operator" in lowered and "why" in lowered:
            return _mock_operations(ctx_lines)
        if "crowd" in lowered and "narrat" in lowered:
            return _mock_crowd(ctx_lines)
        if "volunteer" in lowered:
            return _mock_knowledge(ctx_lines, is_spanish, role="volunteer")
        # default: knowledge / fan
        return _mock_knowledge(ctx_lines, is_spanish, role="fan")


# ---------------------------------------------------------------------------
# Mock narrative helpers
# ---------------------------------------------------------------------------

def _extract_block(text: str, header: str) -> str:
    marker = header
    i = text.find(marker)
    if i == -1:
        return ""
    return text[i + len(marker):]


def _mock_knowledge(ctx_lines, is_spanish: bool, role: str) -> str:
    fact = next((l for l in ctx_lines if l and not l.startswith("Gather")), "")
    if is_spanish:
        if "puerta" in fact.lower() or "gate" in fact.lower():
            return ("Su puerta asignada es la Gate A (North Entrance). Desde su ubicacion actual, "
                    "la ruta mas corta toma ~5 minutos. Nota: Gate B esta congestionada -- le sugiero "
                    "usar Gate D como alternativa (~6 minutos, 80% menos congestion). "
                    "Servicios accesibles disponibles en Gate F. (modo: mock)")
        return ("Pregunta recibida. La informacion disponible indica: " + (fact or "estadio") +
                ". Para asistencia inmediata, busque un voluntario cercano. (modo: mock)")
    return ("Based on the stadium knowledge base: " + (fact or "stadium information available.") +
            " For step-by-step directions, ask 'how do I get to <gate/section>?' or tap Navigate. (mock mode)")


def _mock_navigation(ctx_lines, is_spanish: bool) -> str:
    if is_spanish:
        return ("Ruta sugerida: Gate A → Gate D (~6 min). Congestión en Gate B evitada. "
                "Incluye ruta accesible para silla de ruedas vía Gate F. (modo: mock)")
    return ("Suggested route via Gate D (~6 min, 80% less congestion than Gate B). "
            "Wheelchair-accessible option via Gate F (+1 min). Reasoning: Gate B density >80%, "
            "redirecting to the next-best accessible gate. (mock mode)")


def _mock_crowd(ctx_lines) -> str:
    hot = [l for l in ctx_lines if "%" in l or "gate_" in l][:4]
    return ("Crowd intelligence summary: " + ("; ".join(hot) if hot else "densities nominal across gates") +
            ". Trend: monitor Gate B. Recommendation: pre-position staff at Gate D and keep Gate F "
            "as the accessibility-priority overflow route. (mock mode)")


def _mock_operations(ctx_lines) -> str:
    return ("Queue increase correlates with delayed Metro Line 2 arrivals (see gathered transit data). "
            "Expected normalization in ~18 minutes. Recommended action: open Gate 7/Gate D and dispatch "
            "2 additional stewards. Confidence: medium. (mock mode)")


def _mock_emergency(ctx_lines) -> str:
    return ("EMERGENCY RESPONSE PLAN\n"
            "Immediate actions (0-60s): secure the scene, dispatch nearest medical + security.\n"
            "Nearest exits/medical: see gathered resource list above.\n"
            "Announce calmly in EN/ES/FR/AR. Clear evacuation lanes, stage medical at Gate A/F.\n"
            "Estimated clearance: 12-15 min pending crowd density. (mock mode)")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _split_system(messages: List[LLMMessage]):
    system = ""
    convo = []
    for m in messages:
        if m.role == "system" and not system:
            system = m.content
        else:
            convo.append({"role": m.role, "content": m.content})
    return system, convo


_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is not None:
        return _client
    settings = get_settings()
    if settings.ANTHROPIC_API_KEY:
        try:
            _client = AnthropicClient()
            print("[llm] provider: anthropic")
        except Exception:
            _client = MockLLMClient()
            print("[llm] provider: mock (anthropic init failed)")
    elif settings.OPENAI_API_KEY:
        try:
            _client = OpenAIClient()
            print("[llm] provider: openai")
        except Exception:
            _client = MockLLMClient()
            print("[llm] provider: mock (openai init failed)")
    else:
        _client = MockLLMClient()
        print("[llm] provider: mock (no API key configured)")
    return _client