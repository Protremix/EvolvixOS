#!/usr/bin/env python3
"""Scheduler Pro - APScheduler (MIT) - 100% Free"""
import json, sys, subprocess


class Skill:
    _scheduler = None

    def __init__(self, config: dict = None):
        self.config = config or {}

    def _get_sched(self):
        if Skill._scheduler is None:
            from apscheduler.schedulers.background import BackgroundScheduler
            Skill._scheduler = BackgroundScheduler()
            Skill._scheduler.start()
        return Skill._scheduler

    def run(self, args: dict) -> dict:
        action = args.get("action", "add")
        try:
            sched = self._get_sched()
            if action == "add":
                jtype = args.get("type", "interval")
                jid = args.get("id", f"job_{len(sched.get_jobs())}")
                if jtype == "interval":
                    sched.add_job(func=lambda: None, trigger="interval", seconds=args.get("seconds",60), id=jid)
                elif jtype == "cron":
                    sched.add_job(func=lambda: None, trigger="cron", hour=args.get("hour",0), minute=args.get("minute",0), id=jid)
                return {"status": "scheduled", "id": jid}
            elif action == "list":
                return {"jobs": [{"id": j.id, "next_run": str(j.next_run_time)} for j in sched.get_jobs()]}
            elif action == "remove":
                sched.remove_job(args["id"])
                return {"removed": args["id"]}
            return {"error": f"unknown: {action}"}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "APScheduler"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
