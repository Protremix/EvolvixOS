"""
EvolvixOS — Scheduler Skill
Schedule tasks, reminders, recurring jobs. All local.
100% local using APScheduler. Zero tokens.

Pip: pip install apscheduler
License: MIT (APScheduler)
"""

import os
import json
import time
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from rich.console import Console

console = Console()


class Skill:
    """Scheduler — schedule tasks and reminders. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/scheduled"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._scheduler = None
        self._jobs = {}

    def run(self, args: dict) -> str:
        action = args.get("action", "list")

        if action == "schedule":
            return self.schedule(args.get("command", ""), args.get("when", ""),
                                 args.get("repeat", False))
        elif action == "schedule_interval":
            return self.schedule_interval(args.get("command", ""),
                                          args.get("interval_seconds", 3600))
        elif action == "schedule_cron":
            return self.schedule_cron(args.get("command", ""), args.get("cron", ""))
        elif action == "reminder":
            return self.set_reminder(args.get("message", ""), args.get("when", ""))
        elif action == "list":
            return self.list_jobs()
        elif action == "remove":
            return self.remove_job(args.get("id", ""))
        elif action == "clear":
            return self.clear_all()
        else:
            return (f"Unknown action: {action}. Use: schedule, schedule_interval, "
                    "schedule_cron, reminder, list, remove, clear")

    def _get_scheduler(self):
        if self._scheduler is None:
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                self._scheduler = BackgroundScheduler()
                self._scheduler.start()
            except ImportError:
                return None
        return self._scheduler

    def schedule(self, command: str, when: str, repeat: bool = False) -> str:
        sched = self._get_scheduler()
        if sched is None:
            return "Error: pip install apscheduler"

        try:
            run_time = datetime.fromisoformat(when)
            job_id = f"job_{int(time.time())}"

            if repeat:
                # Daily repeat
                job = sched.add_job(self._run_command, "interval", days=1,
                                    start_date=run_time, args=[command], id=job_id)
            else:
                job = sched.add_job(self._run_command, "date", run_date=run_time,
                                    args=[command], id=job_id)

            self._jobs[job_id] = {
                "command": command,
                "when": when,
                "repeat": repeat,
                "next_run": str(job.trigger.get_next_fire_time(None, datetime.now())),
            }

            return f"Scheduled: {command} for {when} (ID: {job_id})"
        except Exception as e:
            return f"Error: {e}"

    def schedule_interval(self, command: str, interval_seconds: int = 3600) -> str:
        sched = self._get_scheduler()
        if sched is None:
            return "Error: pip install apscheduler"

        try:
            job_id = f"interval_{int(time.time())}"
            job = sched.add_job(self._run_command, "interval", seconds=interval_seconds,
                                args=[command], id=job_id)
            self._jobs[job_id] = {
                "command": command,
                "interval_seconds": interval_seconds,
                "next_run": str(job.trigger.get_next_fire_time(None, datetime.now())),
            }
            return f"Recurring job: {command} every {interval_seconds}s (ID: {job_id})"
        except Exception as e:
            return f"Error: {e}"

    def schedule_cron(self, command: str, cron: str = "") -> str:
        sched = self._get_scheduler()
        if sched is None:
            return "Error: pip install apscheduler"

        try:
            parts = cron.split() if cron else ["*"] * 5
            job_id = f"cron_{int(time.time())}"
            job = sched.add_job(self._run_command, "cron",
                                minute=parts[0] if len(parts) > 0 else "*",
                                hour=parts[1] if len(parts) > 1 else "*",
                                day=parts[2] if len(parts) > 2 else "*",
                                month=parts[3] if len(parts) > 3 else "*",
                                day_of_week=parts[4] if len(parts) > 4 else "*",
                                args=[command], id=job_id)
            self._jobs[job_id] = {
                "command": command,
                "cron": cron,
                "next_run": str(job.trigger.get_next_fire_time(None, datetime.now())),
            }
            return f"Cron job: {command} ({cron}) (ID: {job_id})"
        except Exception as e:
            return f"Error: {e}"

    def set_reminder(self, message: str, when: str) -> str:
        out_file = self.output_dir / f"reminder_{int(time.time())}.json"
        reminder = {
            "message": message,
            "when": when,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }
        out_file.write_text(json.dumps(reminder, indent=2))
        return f"Reminder set: '{message}' for {when}"

    def list_jobs(self) -> str:
        return json.dumps(self._jobs, indent=2) if self._jobs else "No scheduled jobs."

    def remove_job(self, job_id: str) -> str:
        sched = self._get_scheduler()
        if sched and job_id in self._jobs:
            try:
                sched.remove_job(job_id)
            except Exception:
                pass
            del self._jobs[job_id]
            return f"Removed job: {job_id}"
        return f"Job not found: {job_id}"

    def clear_all(self) -> str:
        sched = self._get_scheduler()
        if sched:
            sched.remove_all_jobs()
        count = len(self._jobs)
        self._jobs.clear()
        return f"Cleared {count} jobs."

    def _run_command(self, command: str):
        """Execute a scheduled command."""
        import subprocess
        try:
            subprocess.run(command, shell=True, capture_output=True, timeout=300)
        except Exception as e:
            console.print(f"[red]Scheduled job error: {e}[/red]")
