"""DB reset helper for local/dev.

Usage: python backend/scripts/db_reset.py

This script will:
- If using sqlite (default), back up the file to a timestamped copy
- Remove the sqlite file
- Recreate schema by calling app.db.init_db()

CAUTION: This will destroy data. Use backups.
"""

import os
import shutil
from datetime import datetime

from app.db import get_engine, init_db


def reset_sqlite_db():
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
    if not database_url.startswith('sqlite:///'):
        print('DB reset helper currently supports sqlite only. DATABASE_URL=', database_url)
        return
    path = database_url.replace('sqlite:///', '')
    if not os.path.exists(path):
        print('No sqlite DB file present at', path, ' — creating schema')
        init_db()
        return
    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    backup = f"{path}.backup.{ts}"
    print('Backing up', path, 'to', backup)
    shutil.copy2(path, backup)
    print('Removing', path)
    os.remove(path)
    print('Recreating schema')
    init_db()
    print('Done')


if __name__ == '__main__':
    reset_sqlite_db()
