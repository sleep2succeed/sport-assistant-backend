from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from src.settings import settings

DATA_SCHEMA = "data"


def _conn_info() -> str:
    pg = settings.postgresql
    return (
        f"dbname={pg.DB_NAME} "
        f"user={pg.USERNAME.get_secret_value()} "
        f"password={pg.PASSWORD.get_secret_value()} "
        f"host={pg.HOST} port={pg.PORT}"
    )


# Opened in the FastAPI lifespan, closed on shutdown.
pool = AsyncConnectionPool(conninfo=_conn_info(), min_size=1, max_size=10, open=False)


async def run_migrations() -> None:
    """Apply every .sql file in settings.migrations_dir in lexicographic order.

    All migrations must be idempotent (use IF NOT EXISTS) since they run on
    every startup. Swap for Alembic once schema changes need rollbacks.
    """
    files = sorted(settings.migrations_dir.glob("*.sql"))
    async with pool.connection() as conn, conn.cursor() as cur:
        for path in files:
            await cur.execute(path.read_text())


async def list_tables() -> list[str]:
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name
            """,
            (DATA_SCHEMA,),
        )
        return [row[0] for row in await cur.fetchall()]


async def get_table(name: str, limit: int = 100) -> list[dict]:
    if name not in await list_tables():
        raise ValueError(f"Unknown table: {name}")

    query = sql.SQL("SELECT * FROM {schema}.{table} LIMIT %s").format(
        schema=sql.Identifier(DATA_SCHEMA),
        table=sql.Identifier(name),
    )
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(query, (limit,))
        return list(await cur.fetchall())
