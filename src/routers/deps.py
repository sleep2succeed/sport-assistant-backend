from fastapi import Request
from google_health_api.api import GoogleHealthApi

from langgraph.graph.state import CompiledStateGraph

def get_graph(request: Request) -> CompiledStateGraph:
    return request.app.state.agent_graph


def get_health_api(request: Request) -> GoogleHealthApi:
    return request.app.state.health_api
