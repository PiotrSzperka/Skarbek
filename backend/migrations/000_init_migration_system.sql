-- Migration: Initialize migration tracking system
-- Date: 2025-11-07
-- Description: Creates table to track executed migrations

CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checksum VARCHAR(64),
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_schema_migrations_name ON schema_migrations(migration_name);

-- Record this migration
INSERT INTO schema_migrations (migration_name, executed_at, success) 
VALUES ('000_init_migration_system', NOW(), TRUE)
ON CONFLICT (migration_name) DO NOTHING;
