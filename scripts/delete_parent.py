#!/usr/bin/env python3
"""Delete a parent (and their contributions) by email for local maintenance."""
import argparse
import sys
from pathlib import Path

# Make backend app importable from root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlmodel import delete, select

from app.db import get_db
from app.models import Contribution, Parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Delete a parent and related contributions by email.")
    parser.add_argument("email", help="Email address of the parent to delete.")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without touching the database.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with get_db() as session:
        parent = session.exec(select(Parent).where(Parent.email == args.email)).first()
        if not parent:
            print(f"No parent found with email {args.email}")
            return

        contributions = session.exec(select(Contribution).where(Contribution.parent_id == parent.id)).all()
        print(f"Found parent {parent.name or '<unnamed>'} (ID {parent.id}) with {len(contributions)} contributions.")

        if args.dry_run:
            print("Dry run enabled – nothing will be deleted.")
            return

        if not args.yes:
            confirm = input("Delete this parent and their contributions? [y/N]: ").strip().lower()
            if confirm not in {"y", "yes"}:
                print("Aborted by user.")
                return

        session.exec(delete(Contribution).where(Contribution.parent_id == parent.id))
        session.delete(parent)
        session.commit()
        print("Parent and contributions deleted.")


if __name__ == "__main__":
    main()
