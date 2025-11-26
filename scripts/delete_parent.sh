#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 EMAIL [--dry-run] [--yes]"
  exit 1
      ;;
EMAIL=""
DRY_RUN=false
CONFIRM=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --yes|-y)
      CONFIRM=true
      shift
      ;;
    *)
      if [[ -n "$EMAIL" ]]; then
        echo "Only one email address is supported."
        exit 1
      fi
      EMAIL="$1"
      shift
      ;;
  esac
    print("Parent and contributions deleted.")

if [[ -z "$EMAIL" ]]; then
  echo "Email argument is required."
  exit 1
fi

PYTHONPATH="${PYTHONPATH:-backend}"
export PYTHONPATH

PARENT_EMAIL="$EMAIL"
PARENT_CONFIRM=$([[ "$CONFIRM" == true ]] && echo 1 || echo 0)
PARENT_DRY_RUN=$([[ "$DRY_RUN" == true ]] && echo 1 || echo 0)

python - <<'PY'
import os
from sqlmodel import select, delete
from app.db import get_db
from app.models import Parent, Contribution

email = os.environ['PARENT_EMAIL']
dry_run = os.environ['PARENT_DRY_RUN'] == '1'
confirm = os.environ['PARENT_CONFIRM'] == '1'

with get_db() as session:
    parent = session.exec(select(Parent).where(Parent.email == email)).first()
    if not parent:
        print(f"No parent found with email {email}")
        raise SystemExit(0)
    contributions = session.exec(select(Contribution).where(Contribution.parent_id == parent.id)).all()
    print(f"Found parent {parent.name or '<unnamed>'} (ID {parent.id}) with {len(contributions)} contributions.")
    if dry_run:
        print("Dry run enabled — nothing will be deleted.")
        raise SystemExit(0)
    if not confirm:
        answer = input("Delete this parent and contributions? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Aborted by user.")
            raise SystemExit(0)
    session.exec(delete(Contribution).where(Contribution.parent_id == parent.id))
    session.delete(parent)
    session.commit()
    print("Parent and contributions deleted.")
PY
PY
