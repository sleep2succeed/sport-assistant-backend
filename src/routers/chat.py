from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.routers.deps import get_graph
from src.schemas.chat import (
    ChatResponse,
    Conversation,
    CreateConversationRequest,
    CreateConversationResponse,
    DeleteConversationRequest,
    SendMessageRequest,
)
from src.schemas.llm import OpenAIRequestMessage
from src.services import chat as chat_service
from src.services import conversations
from langgraph.graph.state import CompiledStateGraph

router = APIRouter(prefix="/conversations", tags=["chat"])


@router.post("", response_model=CreateConversationResponse)
async def create_conversation(
    req: CreateConversationRequest,
) -> CreateConversationResponse:
    conv_id = await conversations.create_conversation(req.title)
    return CreateConversationResponse(id=conv_id)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
) -> None:
    await conversations.delete_conversation(conversation_id)


@router.get("", response_model=list[Conversation])
async def list_conversations() -> list[Conversation]:
    return await conversations.load_conversations()


@router.get("/{conversation_id}/messages", response_model=list[OpenAIRequestMessage])
async def list_messages(conversation_id: UUID) -> list[OpenAIRequestMessage]:
    if not await conversations.conversation_exists(conversation_id):
        raise HTTPException(status_code=404, detail="conversation not found")
    return await conversations.load_messages(conversation_id)


@router.post("/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: UUID,
    req: SendMessageRequest,
    graph: CompiledStateGraph = Depends(get_graph),
) -> ChatResponse:
    try:
        reply = await chat_service.send_message(graph, conversation_id, req.content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return ChatResponse(content=reply)
