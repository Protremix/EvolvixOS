"""
EvolvixOS — System Monitor Skill
Monitor CPU, RAM, disk, network, processes. All local.
100% local using psutil. Zero tokens.

Pip: pip install psutil
License: BSD-3 (psutil)
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class Skill:
    """System monitor — CPU, RAM, disk, processes. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/monitor"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, args: dict) -> str:
        action = args.get("action", "overview")

        if action == "overview":
            return self.overview()
        elif action == "cpu":
            return self.cpu_info()
        elif action == "memory":
            return self.memory_info()
        elif action == "disk":
            return self.disk_info()
        elif action == "network":
            return self.network_info()
        elif action == "processes":
            return self.processes(args.get("sort_by", "cpu"), args.get("limit", 20))
        elif action == "kill":
            return self.kill_process(args.get("pid", 0))
        elif action == "battery":
            return self.battery_info()
        elif action == "temperature":
            return self.temperature()
        elif action == "watch":
            return self.watch(args.get("duration", 10), args.get("interval", 1))
        else:
            return (f"Unknown action: {action}. Use: overview, cpu, memory, disk, "
                    "network, processes, kill, battery, temperature, watch")

    def overview(self) -> str:
        try:
            import psutil
            import platform

            result = {
                "hostname": platform.node(),
                "os": f"{platform.system()} {platform.release()}",
                "python_version": platform.python_version(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_count": psutil.cpu_count(),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_total_gb": round(psutil.virtual_memory().total / 1e9, 1),
                "memory_used_gb": round(psutil.virtual_memory().used / 1e9, 1),
                "disk_percent": psutil.disk_usage("/").percent,
                "disk_total_gb": round(psutil.disk_usage("/").total / 1e9, 1),
                "disk_used_gb": round(psutil.disk_usage("/").used / 1e9, 1),
                "uptime_hours": round(time.time() - psutil.boot_time() / 1, 0),
                "process_count": len(psutil.pids()),
            }
            return json.dumps(result, indent=2)
        except ImportError:
            return "Error: pip install psutil"
        except Exception as e:
            return f"Error: {e}"

    def cpu_info(self) -> str:
        try:
            import psutil
            import platform

            result = {
                "cpu_percent": psutil.cpu_percent(interval=1, percpu=True),
                "cpu_count_physical": psutil.cpu_count(logical=False),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "load_avg": psutil.getloadavg() if hasattr(psutil, "getloadavg") else None,
                "architecture": platform.machine(),
                "processor": platform.processor(),
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {e}"

    def memory_info(self) -> str:
        try:
            import psutil
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return json.dumps({
                "virtual": {
                    "total_gb": round(vm.total / 1e9, 1),
                    "available_gb": round(vm.available / 1e9, 1),
                    "used_gb": round(vm.used / 1e9, 1),
                    "percent": vm.percent,
                },
                "swap": {
                    "total_gb": round(swap.total / 1e9, 1),
                    "used_gb": round(swap.used / 1e9, 1),
                    "percent": swap.percent,
                },
            }, indent=2)
        except Exception as e:
            return f"Error: {e}"

    def disk_info(self) -> str:
        try:
            import psutil
            partitions = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total_gb": round(usage.total / 1e9, 1),
                        "used_gb": round(usage.used / 1e9, 1),
                        "free_gb": round(usage.free / 1e9, 1),
                        "percent": usage.percent,
                    })
                except Exception:
                    pass
            return json.dumps({
                "partitions": partitions,
                "io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None,
            }, indent=2, default=str)
        except Exception as e:
            return f"Error: {e}"

    def network_info(self) -> str:
        try:
            import psutil
            io = psutil.net_io_counters()
            connections = len(psutil.net_connections())
            addrs = psutil.net_if_addrs()

            interfaces = {}
            for iface, addr_list in addrs.items():
                interfaces[iface] = [{"family": str(a.family), "address": a.address}
                                    for a in addr_list]

            return json.dumps({
                "bytes_sent": io.bytes_sent,
                "bytes_recv": io.bytes_recv,
                "packets_sent": io.packets_sent,
                "packets_recv": io.packets_recv,
                "active_connections": connections,
                "interfaces": interfaces,
            }, indent=2, default=str)
        except Exception as e:
            return f"Error: {e}"

    def processes(self, sort_by: str = "cpu", limit: int = 20) -> str:
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent",
                                          "status", "username"]):
                try:
                    info = p.info
                    procs.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "cpu_percent": info["cpu_percent"],
                        "memory_percent": round(info["memory_percent"], 1),
                        "status": info["status"],
                        "username": info["username"],
                    })
                except Exception:
                    pass

            # Sort
            sort_key = {"cpu": "cpu_percent", "memory": "memory_percent",
                        "name": "name", "pid": "pid"}.get(sort_by, "cpu_percent")
            reverse = sort_by not in ("name", "pid")
            procs.sort(key=lambda x: x.get(sort_key, 0) or 0, reverse=reverse)

            return json.dumps(procs[:limit], indent=2)
        except Exception as e:
            return f"Error: {e}"

    def kill_process(self, pid: int) -> str:
        try:
            import psutil
            p = psutil.Process(pid)
            name = p.name()
            p.terminate()
            return f"Terminated process {pid} ({name})"
        except psutil.NoSuchProcess:
            return f"Process {pid} not found."
        except Exception as e:
            return f"Error: {e}"

    def battery_info(self) -> str:
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery is None:
                return "No battery detected."
            return json.dumps({
                "percent": battery.percent,
                "plugged": battery.power_plugged,
                "secs_left": battery.secsleft if battery.secsleft != -1 else "unlimited",
            }, indent=2)
        except Exception as e:
            return f"Error: {e}"

    def temperature(self) -> str:
        try:
            import psutil
            temps = psutil.sensors_temperatures()
            if not temps:
                return "No temperature sensors available."
            result = {}
            for name, entries in temps.items():
                result[name] = [{"label": e.label, "current": e.current,
                                 "high": e.high, "critical": e.critical}
                                for e in entries]
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return f"Error: {e}"

    def watch(self, duration: int = 10, interval: int = 1) -> str:
        """Monitor system for a duration and return samples."""
        try:
            import psutil
            samples = []
            for _ in range(int(duration / interval)):
                samples.append({
                    "timestamp": time.time(),
                    "cpu_percent": psutil.cpu_percent(interval=interval),
                    "memory_percent": psutil.virtual_memory().percent,
                })
            avg_cpu = sum(s["cpu_percent"] for s in samples) / len(samples)
            avg_mem = sum(s["memory_percent"] for s in samples) / len(samples)
            return json.dumps({
                "duration_seconds": duration,
                "samples": len(samples),
                "avg_cpu_percent": round(avg_cpu, 1),
                "avg_memory_percent": round(avg_mem, 1),
            }, indent=2)
        except Exception as e:
            return f"Error: {e}"
