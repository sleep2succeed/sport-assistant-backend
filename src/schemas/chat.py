from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ChatResponse(BaseModel):
    content: str


class ProxyIpResponse(BaseModel):
    ip: str


class CreateConversationRequest(BaseModel):
    title: str | None = None


class CreateConversationResponse(BaseModel):
    id: UUID


class DeleteConversationRequest(BaseModel):
    id: UUID


class SendMessageRequest(BaseModel):
    content: str


class Conversation(BaseModel):
    id: UUID
    title: str | None = None

class ConversationList(BaseModel):
    conversation_list: list[Conversation] | None = None
    total: int = 0
