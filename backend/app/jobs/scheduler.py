from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from app.jobs.run_all_once import run_once


def main() -> None:
    interval_sec = int(os.getenv("POLL_INTERVAL_SECONDS", "120"))
    print(f"scheduler started: interval={interval_sec}s")

    while True:
        started = datetime.now(timezone.utc).isoformat()
        try:
            print(f"[{started}] tick")
            run_once()
        except Exception as e:
            print(f"[{started}] scheduler tick failed: {e}")
        time.sleep(interval_sec)


if __name__ == "__main__":
    main()
