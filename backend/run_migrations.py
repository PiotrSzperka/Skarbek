#!/usr/bin/env python3
"""
Migration runner - executes pending SQL migrations in order
"""
import os
import sys
import time
import hashlib
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
DB_URL = os.getenv("DATABASE_URL", "postgresql://skarbek:skarbek@localhost:5432/skarbek")


def get_db_connection():
    """Get database connection using psycopg2."""
    # Database URL from environment or default
    db_url = os.getenv('DATABASE_URL', 'postgresql://skarbek:skarbek@localhost:5432/skarbek')
    
    # psycopg2 doesn't understand SQLAlchemy's +psycopg2 dialect
    # Convert postgresql+psycopg2:// to postgresql://
    db_url = db_url.replace('postgresql+psycopg2://', 'postgresql://')
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False  # We want explicit transaction control
        return conn
    except Exception as e:
        raise Exception(f"Cannot connect to database: {e}")


def calculate_checksum(filepath):
    """Calculate SHA256 checksum of migration file"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()


def get_executed_migrations(conn):
    """Get set of already executed migration names"""
    with conn.cursor() as cur:
        # Check if schema_migrations table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'schema_migrations'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            return set()
        
        cur.execute("SELECT migration_name FROM schema_migrations WHERE success = TRUE")
        return {row[0] for row in cur.fetchall()}


def get_pending_migrations(executed):
    """Get list of pending migrations sorted by filename"""
    all_migrations = sorted([
        f for f in MIGRATIONS_DIR.glob("*.sql")
        if f.is_file()
    ])
    
    pending = []
    for migration_file in all_migrations:
        migration_name = migration_file.stem
        if migration_name not in executed:
            pending.append(migration_file)
    
    return pending


def execute_migration(conn, migration_file):
    """Execute a single migration file"""
    migration_name = migration_file.stem
    checksum = calculate_checksum(migration_file)
    
    print(f"\n▶ Executing migration: {migration_name}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    start_time = time.time()
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        print(f"  ✓ Success ({execution_time_ms}ms)")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"  ✗ FAILED: {e}")
        
        # Try to record failure
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO schema_migrations (migration_name, checksum, success) 
                    VALUES (%s, %s, FALSE)
                    ON CONFLICT (migration_name) DO NOTHING
                """, (migration_name, checksum))
            conn.commit()
        except:
            pass
        
        return False


def run_migrations():
    """Main migration runner"""
    print("=" * 60)
    print("DATABASE MIGRATION RUNNER")
    print("=" * 60)
    
    conn = get_db_connection()
    
    try:
        executed = get_executed_migrations(conn)
        print(f"\n📊 Executed migrations: {len(executed)}")
        
        pending = get_pending_migrations(executed)
        print(f"📋 Pending migrations: {len(pending)}")
        
        if not pending:
            print("\n✓ Database is up to date!")
            return 0
        
        print(f"\n🚀 Running {len(pending)} migration(s)...\n")
        
        failed = []
        for migration_file in pending:
            success = execute_migration(conn, migration_file)
            if not success:
                failed.append(migration_file.name)
                print(f"\n⚠ Stopping due to migration failure")
                break
        
        if failed:
            print(f"\n❌ {len(failed)} migration(s) FAILED:")
            for name in failed:
                print(f"   - {name}")
            return 1
        
        print(f"\n✓ All migrations completed successfully!")
        return 0
        
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(run_migrations())
