from fastapi import APIRouter, Depends
from google_health_api.api import GoogleHealthApi
from langchain_core.messages import HumanMessage

from src.routers.deps import get_health_api, get_graph
from src.schemas.agent import AgentState
from src.schemas.health import AskHealthRequest, AskHealthResponse
from langgraph.graph.state import CompiledStateGraph

router = APIRouter(prefix="/health-agent", tags=["health"])


@router.post("/ask", response_model=AskHealthResponse)
async def ask_health(
    req: AskHealthRequest,
    graph: CompiledStateGraph = Depends(get_graph),
) -> AskHealthResponse:
    answer = await graph.ainvoke(
        AgentState(messages=[HumanMessage(content=req.question)])
        )
    return AskHealthResponse(answer=answer)
