# Sport coach and doctor

Agentic AI-assistant with access to Google Fitbit metrics

## Running the app

1. Start Postgres (once; container persists across restarts):
   ```bash
   docker run -d --name climbing-assistant-postgres \
     -e POSTGRES_USER=<POSTGRESQL__USERNAME from .env> \
     -e POSTGRES_PASSWORD=<POSTGRESQL__PASSWORD from .env> \
     -e POSTGRES_DB=climbing_assistant \
     -p 5432:5432 \
     postgres:16
   ```
   If the container already exists, just start it again: `docker start climbing-assistant-postgres`.
2. Make sure `client_secret.json` and `token.json` exist at the repo root (Google Health OAuth — see `notebooks/fitbit_analysis.ipynb` for the one-time login flow).
3. Run the server:
   ```bash
   uv run uvicorn src.main:app --reload
   # or
   uv run python -m src.main --reload
   ```
   Server listens on `http://localhost:8000` by default (`--host`/`--port` flags available on the `python -m src.main` entrypoint).

## Stopping / releasing port 8000

- If you started uvicorn in the foreground, `Ctrl+C` stops it and frees the port.
- If it's running in the background or got orphaned:
  ```bash
  lsof -ti:8000 | xargs kill
  ```
- To stop Postgres (frees port 5432): `docker stop climbing-assistant-postgres` (add `docker rm` to delete the container entirely).

## Testing

### curl
```bash
curl -X POST localhost:8000/health-agent/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "How many steps did I take yesterday?"}'
```

### Debugger (VS Code)
Add to `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI: uvicorn",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["src.main:app", "--reload", "--port", "8000"],
      "jinja": true,
      "justMyCode": false,
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```
Set breakpoints in `src/services/fitbit_agent.py`, `src/services/health_tools.py`, etc., then hit F5 and trigger a request via curl or a notebook cell. `--reload` works fine with the debugger; just re-hit the endpoint after edits.

### Jupyter notebook
Two options:

**A. Hit the real running server** (simplest — just needs `uv run uvicorn ...` running in a terminal):
```python
import httpx

resp = httpx.post(
    "http://localhost:8000/health-agent/ask",
    json={"question": "How did I sleep last night?"},
    timeout=30.0,  # tool-calling round-trips (LLM + Google Health API) can take 5-10s+, above httpx's default 5s
)
resp.json()
```

**B. Call the FastAPI app in-process** (no server needed, but skips the `lifespan` DB pool/health API setup — best for testing routers/schemas without infra, not for testing `app.state`-dependent endpoints unless you replicate lifespan manually):
```python
import httpx
from src.main import app

async with httpx.AsyncClient(
    transport=httpx.ASGITransport(app=app), base_url="http://test"
) as client:
    resp = await client.post("/health-agent/ask", json={"question": "..."})
    print(resp.json())
```
Since `/health-agent/ask` depends on `app.state.llm`/`app.state.health_api` set up in `lifespan`, prefer option A unless you also run `async with app.router.lifespan_context(app):` around the client block.

For testing individual tool functions or the Google Health client directly (bypassing FastAPI entirely), see the existing pattern in `notebooks/fitbit_analysis.ipynb` — build `GoogleHealthApi`/`OpenAIClient` directly and call `src/services/health_tools.py` functions or `src/services/fitbit_agent.ask(...)`.