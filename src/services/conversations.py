from uuid import UUID

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from src.schemas.chat import Conversation, ConversationList
from src.schemas.llm import OpenAIRequestMessage, OpenAIRoles
from src.services.db import pool


async def create_conversation(title: str | None = None) -> UUID:
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO app.conversations (title) VALUES (%s) RETURNING id",
            (title,),
        )
        row = await cur.fetchone()
        assert row is not None
        return row[0]


async def delete_conversation(conversation_id: str | None = None) -> None:
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "DELETE FROM app.conversations WHERE id = %s;",
            (conversation_id,),
        )
        await cur.execute(
            "DELETE FROM app.messages WHERE conversation_id = %s;",
            (
                conversation_id,
            ),
        )


async def append_message(conversation_id: UUID, message: OpenAIRequestMessage) -> None:
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO app.messages
                (conversation_id, role, content, tool_calls, tool_call_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                conversation_id,
                str(message.role),
                message.content,
                Jsonb(message.tool_calls) if message.tool_calls is not None else None,
                message.tool_call_id,
            ),
        )


async def load_conversations(limit: int = 10) -> list[Conversation]:
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id, title
            FROM app.conversations
            ORDER BY id
            LIMIT %s
            """,
            (limit,),
        )
        rows = await cur.fetchall()

        return  [
                    Conversation(
                        id=row["id"],
                        title=row["title"]
                    )
                    for row in rows
                ]



async def load_messages(conversation_id: UUID) -> list[OpenAIRequestMessage]:
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT role, content, tool_calls, tool_call_id
            FROM app.messages
            WHERE conversation_id = %s
            ORDER BY id
            """,
            (conversation_id,),
        )
        rows = await cur.fetchall()

    return [
        OpenAIRequestMessage(
            role=OpenAIRoles(row["role"]),
            content=row["content"],
            tool_calls=row["tool_calls"],
            tool_call_id=row["tool_call_id"],
        )
        for row in rows
    ]


async def conversation_exists(conversation_id: UUID) -> bool:
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "SELECT 1 FROM app.conversations WHERE id = %s",
            (conversation_id,),
        )
        return await cur.fetchone() is not None
