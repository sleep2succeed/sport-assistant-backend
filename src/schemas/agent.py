import operator
from typing import Annotated

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    total_tokens: Annotated[int, operator.add] = 0