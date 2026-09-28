from uuid import UUID

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph

from src.schemas.llm import OpenAIRequestMessage, OpenAIRoles
from src.services import conversations


def _to_lc(message: OpenAIRequestMessage) -> HumanMessage | AIMessage:
    if message.role == OpenAIRoles.USER:
        return HumanMessage(content=message.content or "")
    if message.role == OpenAIRoles.ASSISTANT:
        return AIMessage(content=message.content or "")
    raise ValueError(f"Unsupported role for storage: {message.role}")


async def send_message(
    graph: CompiledStateGraph,
    conversation_id: UUID,
    user_content: str,
) -> str:
    """Append user turn, invoke the agent graph, persist and return the reply."""
    if not await conversations.conversation_exists(conversation_id):
        raise ValueError(f"Unknown conversation: {conversation_id}")

    await conversations.append_message(
        conversation_id,
        OpenAIRequestMessage(role=OpenAIRoles.USER, content=user_content),
    )

    history = await conversations.load_messages(conversation_id)
    final_state = await graph.ainvoke({"messages": [_to_lc(m) for m in history]})

    assistant_message: AIMessage | None = None
    for message in reversed(final_state.get("messages", [])):
        if isinstance(message, AIMessage):
            assistant_message = message
            break

    if assistant_message is None:
        return ""

    reply = assistant_message.content or ""
    await conversations.append_message(
        conversation_id,
        OpenAIRequestMessage(role=OpenAIRoles.ASSISTANT, content=reply),
    )
    return reply
