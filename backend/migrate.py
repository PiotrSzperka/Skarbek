#!/usr/bin/env python3
"""
Database migration runner with audit tracking.

Usage:
    python migrate.py              # Run all pending migrations
    python migrate.py --dry-run    # Show pending migrations without applying
    python migrate.py --status     # Show migration status
"""

import os
import sys
import time
import hashlib
from pathlib import Path

# psycopg2 is used directly in DATABASE_URL, so it should be installed
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("Error: psycopg2 not installed. Install with: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)

MIGRATIONS_DIR = Path(__file__).parent / 'migrations'


def get_connection():
    """Get direct psycopg2 connection from environment variables"""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'db'),
        port=int(os.getenv('DB_PORT', 5432)),
        dbname=os.getenv('POSTGRES_DB', 'skarbek'),
        user=os.getenv('POSTGRES_USER', 'skarbek'),
        password=os.getenv('POSTGRES_PASSWORD', 'skarbek')
    )
    return conn


def calculate_checksum(filepath):
    """Calculate SHA256 checksum of migration file"""
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def init_migrations_table(conn):
    """Ensure schema_migrations table exists"""
    with conn.cursor() as cur:
        init_file = MIGRATIONS_DIR / '000_init_migrations.sql'
        if init_file.exists():
            with open(init_file, 'r') as f:
                cur.execute(f.read())
    conn.commit()


def get_applied_migrations(conn):
    """Get set of already applied migration names"""
    with conn.cursor() as cur:
        cur.execute("SELECT migration_name FROM schema_migrations ORDER BY applied_at")
        return {row[0] for row in cur.fetchall()}


def get_pending_migrations(applied):
    """Get list of pending migration files"""
    all_migrations = sorted([
        f for f in MIGRATIONS_DIR.glob('*.sql')
        if f.name != '000_init_migrations.sql'
    ])
    
    pending = []
    for migration_file in all_migrations:
        if migration_file.stem not in applied:
            pending.append(migration_file)
    
    return pending


def apply_migration(conn, migration_file):
    """Apply a single migration and record it"""
    migration_name = migration_file.stem
    checksum = calculate_checksum(migration_file)
    
    print(f"Applying migration: {migration_name}")
    
    start_time = time.time()
    
    with conn.cursor() as cur:
        # Read and execute migration
        with open(migration_file, 'r') as f:
            sql = f.read()
            cur.execute(sql)
        
        # Record in audit table
        elapsed_ms = int((time.time() - start_time) * 1000)
        cur.execute(
            """
            INSERT INTO schema_migrations (migration_name, checksum, execution_time_ms)
            VALUES (%s, %s, %s)
            """,
            (migration_name, checksum, elapsed_ms)
        )
    
    conn.commit()
    print(f"  ✓ Applied in {elapsed_ms}ms")


def show_status(conn):
    """Show migration status"""
    applied = get_applied_migrations(conn)
    all_migrations = sorted([
        f for f in MIGRATIONS_DIR.glob('*.sql')
        if f.name != '000_init_migrations.sql'
    ])
    
    print("\nMigration Status:")
    print("-" * 60)
    
    for migration_file in all_migrations:
        name = migration_file.stem
        status = "✓ Applied" if name in applied else "⧗ Pending"
        print(f"{status:12} {name}")
    
    pending_count = len([m for m in all_migrations if m.stem not in applied])
    print("-" * 60)
    print(f"Total: {len(all_migrations)} migrations, {len(applied)} applied, {pending_count} pending\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run database migrations')
    parser.add_argument('--dry-run', action='store_true', help='Show pending migrations without applying')
    parser.add_argument('--status', action='store_true', help='Show migration status')
    args = parser.parse_args()
    
    conn = None
    try:
        conn = get_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Initialize migrations table
        init_migrations_table(conn)
        
        if args.status:
            show_status(conn)
            return 0
        
        # Get applied and pending migrations
        applied = get_applied_migrations(conn)
        pending = get_pending_migrations(applied)
        
        if not pending:
            print("No pending migrations.")
            return 0
        
        if args.dry_run:
            print(f"\nPending migrations ({len(pending)}):")
            for m in pending:
                print(f"  - {m.stem}")
            return 0
        
        # Apply pending migrations
        print(f"\nApplying {len(pending)} pending migration(s)...\n")
        for migration_file in pending:
            apply_migration(conn, migration_file)
        
        print(f"\n✓ All migrations applied successfully.\n")
        return 0
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    sys.exit(main())
