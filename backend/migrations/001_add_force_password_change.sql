-- Migration: Add force_password_change fields to Parent table
-- Date: 2025-11-07
-- Description: Adds force_password_change flag and password_changed_at timestamp to support mandatory password change on first login

-- Check if already executed
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE migration_name = '001_add_force_password_change') THEN
        RAISE NOTICE 'Migration 001_add_force_password_change already executed, skipping';
        RETURN;
    END IF;
END $$;

-- Execute migration
ALTER TABLE parent ADD COLUMN IF NOT EXISTS force_password_change boolean DEFAULT true;
ALTER TABLE parent ADD COLUMN IF NOT EXISTS password_changed_at timestamp with time zone NULL;

-- Set existing parents to not require password change (already have active accounts)
UPDATE parent SET force_password_change = false WHERE force_password_change IS NULL OR password_hash IS NOT NULL;

-- Record migration
INSERT INTO schema_migrations (migration_name, executed_at, success) 
VALUES ('001_add_force_password_change', NOW(), TRUE)
ON CONFLICT (migration_name) DO NOTHING;
