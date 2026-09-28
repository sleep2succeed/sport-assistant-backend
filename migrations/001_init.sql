-- Two schemas separate user-facing crawl data from operational state.
--
--   data.* : tables exposed via GET /tables and GET /tables/{name}
--   app.*  : conversations, messages, and other internal state (hidden)
--
-- gen_random_uuid() is built into Postgres 13+, no extension needed.

CREATE SCHEMA IF NOT EXISTS data;
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS data.parsed_sources (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT,
    crawled_at  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS app.conversations (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title      TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.messages (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES app.conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,
    content         TEXT,
    tool_calls      JSONB,
    tool_call_id    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS messages_conv_id_idx
    ON app.messages (conversation_id, id);
