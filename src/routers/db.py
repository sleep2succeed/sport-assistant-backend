from fastapi import APIRouter, HTTPException, Query

from src.services import db

router = APIRouter(prefix="/tables", tags=["db"])


@router.get("", response_model=list[str])
async def list_tables() -> list[str]:
    try:
        return await db.list_tables()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}", response_model=list[dict])
async def fetch_table(
    name: str, limit: int = Query(500, ge=1, le=10_000)
) -> list[dict]:
    try:
        return await db.get_table(name, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
