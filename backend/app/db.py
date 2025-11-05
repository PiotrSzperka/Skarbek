from sqlmodel import SQLModel, create_engine, Session, select
import os
from sqlalchemy import inspect, text
from .models import AdminUser
from .auth import hash_password


def get_engine():
    # Read DATABASE_URL at runtime so Docker/ENV can control it
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    return create_engine(database_url, echo=False)


def init_db():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    # Ensure new columns exist in existing DBs (lightweight, idempotent)
    # This avoids crashing when running against an older database without
    # performing full migrations. It attempts to add the admin-facing
    # columns we introduced (parent.is_hidden, campaign.is_closed,
    # campaign.deleted_at) when they are missing.
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        with engine.connect() as conn:
            # parent.is_hidden
            if 'parent' in tables:
                cols = [c['name'] for c in inspector.get_columns('parent')]
                if 'is_hidden' not in cols:
                    try:
                        conn.execute(text('ALTER TABLE parent ADD COLUMN is_hidden boolean DEFAULT false'))
                    except Exception:
                        # best-effort: ignore if cannot alter (e.g., permissions)
                        pass

            # campaign.is_closed and campaign.deleted_at
            if 'campaign' in tables:
                cols = [c['name'] for c in inspector.get_columns('campaign')]
                if 'is_closed' not in cols:
                    try:
                        conn.execute(text("ALTER TABLE campaign ADD COLUMN is_closed boolean DEFAULT false"))
                    except Exception:
                        pass
                if 'deleted_at' not in cols:
                    try:
                        # timestamp with time zone is safe for postgres; sqlite will accept a generic DATETIME
                        conn.execute(text("ALTER TABLE campaign ADD COLUMN deleted_at TIMESTAMP NULL"))
                    except Exception:
                        pass
    except Exception:
        # keep init_db resilient; don't break app startup if inspection fails
        pass
    # Seed default admin user for dev if not present
    admin_username = os.getenv("ADMIN_USER", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "changeme")
    with Session(engine) as session:
        existing = session.exec(select(AdminUser).where(AdminUser.username == admin_username)).first()
        if not existing:
            user = AdminUser(username=admin_username, password_hash=hash_password(admin_password))
            session.add(user)
            session.commit()


def get_db():
    engine = get_engine()
    return Session(engine)
