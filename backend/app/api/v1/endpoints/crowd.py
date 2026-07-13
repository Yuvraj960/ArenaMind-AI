from fastapi import APIRouter
from app.models.schemas import (
    CrowdHeatmapResponse,
    CrowdHeatmapPoint,
    CrowdDensity,
    CrowdPredictionsResponse,
    CrowdPrediction,
)
from app.simulators.stadium_simulator import get_simulator
from app.agents.crowd_agent import CrowdAgent
from app.agents.base_agent import AgentRequest
from app.models.schemas import AgentType

router = APIRouter()
crowd_agent = CrowdAgent()


@router.get("/heatmap", response_model=CrowdHeatmapResponse)
async def get_heatmap():
    """Get the live crowd heatmap + GenAI narrative over simulated gate/section densities."""
    simulator = get_simulator()
    heatmap_points = [
        CrowdHeatmapPoint(**p) for p in simulator.get_crowd_heatmap()
    ]
    densities = [CrowdDensity(**d) for d in simulator.get_gate_densities()]

    high = sum(1 for d in densities if d.density_percentage > 70)
    if high > 2:
        overall = "critical"
    elif high > 0:
        overall = "elevated"
    else:
        overall = "normal"

    return CrowdHeatmapResponse(
        stadium_id="fifa_wc_2026_stadium_1",
        heatmap=heatmap_points,
        gates=densities,
        narrative=simulator.generate_narrative(),
        overall_status=overall,
    )


@router.get("/gates", response_model=list[CrowdDensity])
async def get_gate_densities():
    """Current density at every gate."""
    simulator = get_simulator()
    return [CrowdDensity(**d) for d in simulator.get_gate_densities()]


@router.post("/predict", response_model=CrowdPredictionsResponse)
async def predict_congestion(gate_ids: list[str], horizon_minutes: int = 15):
    """Predict congestion at the given gates over the next N minutes."""
    simulator = get_simulator()
    densities = {d["gate_id"]: d for d in simulator.get_gate_densities()}

    predictions = []
    for gate_id in gate_ids:
        gate_data = densities.get(gate_id)
        if not gate_data:
            continue
        current = gate_data["density_percentage"]
        trend = gate_data["trend"]
        if trend == "increasing":
            predicted = min(100, current * 1.3)
        elif trend == "decreasing":
            predicted = max(0, current * 0.7)
        else:
            predicted = current

        if predicted > 80:
            risk = "high"
            action = "URGENT: redirect flow to alternative gates, deploy additional staff"
        elif predicted > 50:
            risk = "medium"
            action = "Monitor closely, prepare contingency routing"
        else:
            risk = "low"
            action = "Normal monitoring sufficient"

        predictions.append(CrowdPrediction(
            gate_id=gate_id,
            current_density=current,
            predicted_density=round(predicted, 1),
            trend=trend,
            risk_level=risk,
            recommended_action=action,
        ))

    return CrowdPredictionsResponse(predictions=predictions, horizon_minutes=horizon_minutes)


@router.post("/query")
async def query_crowd(question: str):
    """Natural-language crowd intelligence query (GenAI narrative)."""
    result = await crowd_agent.execute(AgentRequest(
        agent_type=AgentType.CROWD,
        payload={"question": question, "query_type": "narrative"},
    ))
    return result.result