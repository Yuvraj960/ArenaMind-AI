from typing import Dict, Any, List

from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentType


class TranslationAgent(BaseAgent):
    """Thin translation wrapper. In a real deployment, Claude handles all language tasks
    natively; this agent provides consistent phrase dictionaries and emergency templates."""

    def __init__(self):
        super().__init__(AgentType.TRANSLATION)

    def get_system_prompt(self) -> str:
        return (
            "You are the ArenaMind Translation Agent for FIFA World Cup 2026.Translate from source "
            "language to target language preserving stadium terminology, directional language, and tone. "
            "For emergency context preserve absolute clarity. Return only the translation."
        )

    async def gather_data(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        text = payload.get("text", "")
        target = payload.get("target_language", "en")
        ctx = payload.get("context", "general")
        phrases = self._emergency_phrases(target)

        context_text = (
            f"Source text: {text}\n"
            f"Target language: {target} ({self._lang_name(target)})\n"
            f"Context: {ctx}\n"
            f"Emergency phrases: {phrases}"
        )
        return {
            "context_text": context_text,
            "original": text,
            "target_language": target,
            "context": ctx,
            "phrases": phrases,
            "tools_used": [],
        }

    def _lang_name(self, code: str) -> str:
        return {"en": "English", "es": "Spanish", "fr": "French", "de": "German",
                "pt": "Portuguese", "ar": "Arabic", "zh": "Chinese", "ja": "Japanese"}.get(code, code)

    def _emergency_phrases(self, lang: str) -> Dict[str, str]:
        base = {
            "evacuate_now": "Evacuate immediately via the nearest exit.",
            "stay_calm": "Please remain calm and follow staff instructions.",
            "medical_emergency": "Medical emergency reported. Medical team dispatched.",
            "suspicious_object": "Security alert. Do not touch suspicious items. Report to staff.",
            "severe_weather": "Severe weather warning. Seek covered areas immediately.",
            "gate_closed": "This gate is temporarily closed. Please proceed to the indicated alternative.",
            "assistance_available": "Assistance available at Gate F for accessibility needs.",
        }
        es = {
            "evacuate_now": "Evacúe inmediatamente por la salida más cercana.",
            "stay_calm": "Por favor, mantenga la calma y siga las instrucciones del personal.",
            "medical_emergency": "Emergencia médica reportada. Equipo médico enviado.",
            "suspicious_object": "Alerta seguridad. No toque objetos sospechosos. Reporte al personal.",
            "severe_weather": "Advertencia de clima severo. Busque áreas cubiertas inmediatamente.",
            "gate_closed": "Esta puerta está temporalmente cerrada. diríjase a la alternativa indicada.",
            "assistance_available": "Asistencia disponible en Puerta F para necesidades de accesibilidad.",
        }
        if lang == "es":
            return es
        return base