from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI

import sys

from src.agents.graph import build_agent_graph
  
# adding src to the system path
sys.path.insert(0, '/Users/a.son/climbing-assistant-backend')

from src.routers import chat, db
from src.services.db import pool, run_migrations
from src.services.google_health_client import build_health_api
from src.services.llm import build_chat_model
from src.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await pool.open()
    await run_migrations()

    app.state.llm = build_chat_model(settings.llm)
    app.state.health_session = aiohttp.ClientSession()
    app.state.health_api = build_health_api(app.state.health_session, settings.google_health)
    app.state.agent_graph = build_agent_graph(app.state.llm, app.state.health_api)
    try:
        yield
    finally:
        await app.state.health_session.close()
        await pool.close()


app = FastAPI(title="Sport Assistant Backend", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(db.router)
app.include_router(chat.router)


def main() -> None:
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run(
        "src.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
