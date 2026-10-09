"""Wait until MySQL accepts connections. Used by Docker before seed + uvicorn."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.database.connection import wait_for_db  # noqa: E402

if __name__ == "__main__":
    print("Waiting for MySQL...")
    wait_for_db()
    print("MySQL is ready.")
