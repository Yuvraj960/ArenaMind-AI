from fastapi import APIRouter
from app.models.schemas import OperationsQuery, OperationsResponse
from app.agents.operations_agent import OperationsAgent
from app.agents.base_agent import AgentRequest
from app.models.schemas import AgentType

router = APIRouter()
operations_agent = OperationsAgent()


@router.post("/query", response_model=OperationsResponse)
async def operations_query(query: OperationsQuery):
    """
    Natural-language operations copilot. Operator asks a question; the AI analyzes
    crowd, transit, weather, staff deployment, and SOPs, and returns a grounded answer
    with recommended actions.
    """
    try:
        result = await operations_agent.execute(AgentRequest(
            agent_type=AgentType.OPERATIONS,
            payload={
                "question": query.question,
                "context": query.context,
                "role": query.role.value if hasattr(query.role, "value") else str(query.role),
            },
        ))

        text = result.result.get("response", "") or str(result.result)
        return OperationsResponse(
            success=True,
            answer=text,
            data_sources=result.result.get("data_sources", ["crowd", "transit", "weather", "staff", "sops"]),
            confidence=result.confidence,
            recommended_actions=result.result.get("recommended_actions", []),
            related_metrics=result.result.get("related_metrics", {}),
        )
    except Exception as e:
        return OperationsResponse(
            success=False,
            answer=f"Operations copilot is temporarily unavailable. Please consult the operations dashboard directly. (Error: {str(e)})",
            data_sources=[],
            confidence=0.0,
            recommended_actions=["Check operations dashboard", "Contact duty supervisor"],
            related_metrics={},
        )