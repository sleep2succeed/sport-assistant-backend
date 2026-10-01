from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from google_health_api.api import GoogleHealthApi

from src.schemas.agent import AgentState
from src.services.health_tools import LOCAL_TZ, build_health_tools

FITBIT_SYSTEM_PROMPT = (
    "You are a health data assistant with access to the user's Google Health data "
    "(steps, heart rate, sleep, activity, resting heart rate and HRV). "
    "IMPORTANT: before computing any time range, call `get_current_time_tool` to get the "
    "current local date and time. Then compute start_time/end_time relative to that "
    "timestamp and pass them as ISO-8601 strings including the UTC offset "
    f"({LOCAL_TZ.key}). Never guess the current date. "
    "When a question refers to a relative period ('yesterday', 'last night', "
    "'this week', 'last 7 days'), compute start_time/end_time from the value returned "
    "by `get_current_time_tool` and pass them explicitly rather than omitting them. "
    "Use the available tools to fetch the data you need, then answer the user's "
    "question clearly and concisely based on that data."
)


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
            system_prompt=FITBIT_SYSTEM_PROMPT,
        ),
    )
    graph.add_edge(START, "fitbit_agent")
    graph.add_edge("fitbit_agent", END)
    return graph.compile()
