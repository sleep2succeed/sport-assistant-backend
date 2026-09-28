from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from google_health_api.api import GoogleHealthApi

from src.schemas.agent import AgentState
from src.services.health_tools import build_health_tools


def build_agent_graph(
    llm: BaseChatModel,
    api: GoogleHealthApi,
) -> CompiledStateGraph[AgentState, Any, Any, Any]:
    graph = StateGraph(AgentState)
    graph.add_node(
        "fitbit_agent",
        create_agent(
            model=llm,
            tools=build_health_tools(api),
            state_schema=AgentState,
        ),
    )
    graph.add_edge(START, "fitbit_agent")
    graph.add_edge("fitbit_agent", END)
    return graph.compile()
