"""
scheduler.py — Simple daily scheduler using APScheduler.
It reads SCHEDULE_HOUR and SCHEDULE_MINUTE from .env and schedules
main.run_once() at that time every day.
"""

import os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

# Import the main orchestration function lazily to avoid heavy imports at import time
def _run_job():
    from .main import run_once
    print(f"[SCHEDULER] Running job at {datetime.now().isoformat()}")
    run_once()


def start_scheduler():
    hour   = int(os.getenv("SCHEDULE_HOUR", "8"))
    minute = int(os.getenv("SCHEDULE_MINUTE", "0"))
    scheduler = BlockingScheduler()
    scheduler.add_job(_run_job, "cron", hour=hour, minute=minute, id="daily_digest")
    print(f"[SCHEDULER] Scheduled daily digest for {hour:02d}:{minute:02d}")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("[SCHEDULER] Stopped by user")

if __name__ == "__main__":
    start_scheduler()
