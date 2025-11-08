-- Migration system initialization
-- Creates audit table for tracking migrations

CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checksum VARCHAR(64),
    execution_time_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_schema_migrations_name ON schema_migrations(migration_name);
