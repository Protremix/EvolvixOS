"""
EvolvixOS — Platform Dashboard
Unified web dashboard for the AI Engineering Platform.

Serves a single-page app that provides:
  - System overview (skills, models, pipelines, experiments)
  - Model registry management
  - Experiment tracking
  - Pipeline builder & execution
  - Model serving & metrics
  - Evaluation results
  - GitHub Discovery status
  - Server management (Hetzner)

Run: python platform/dashboard.py
Port: 5000
"""

import os
import json
import sys
from flask import Flask, send_from_directory, jsonify, request

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__, static_folder="static")

# Import API server components (lazy)
_api = None

def get_api():
    global _api
    if _api is None:
        from api_server import EvolvixAPI
        _api = EvolvixAPI()
        _api._init_skills()
    return _api


@app.route("/")
def index():
    """Serve the dashboard."""
    return send_from_directory("static", "index.html")


@app.route("/app")
def app_page():
    """Serve the PWA app."""
    return send_from_directory("static", "app.html")


@app.route("/api/dashboard/overview")
def dashboard_overview():
    """Get full platform overview."""
    api = get_api()
    skills = api._skills

    # Gather stats
    overview = {
        "skills": {
            "total": len(skills),
            "names": list(skills.keys()),
        },
        "models": {},
        "experiments": {},
        "pipelines": {},
        "servers": {},
        "cost": "$0.00",
        "version": "0.4",
    }

    # Model registry
    if "model_registry" in skills:
        try:
            import importlib
            reg = skills["model_registry"]
            reg_data = reg.registry
            overview["models"] = {
                "total": len(reg_data.get("models", {})),
                "deployed": len(reg_data.get("deployed", {})),
            }
        except:
            overview["models"] = {"total": 0, "deployed": 0}

    # Experiments
    if "experiment_tracker" in skills:
        try:
            exp = skills["experiment_tracker"]
            exps = exp.data.get("experiments", {})
            overview["experiments"] = {
                "total": len(exps),
                "running": sum(1 for e in exps.values() if e.get("status") == "running"),
                "completed": sum(1 for e in exps.values() if e.get("status") == "completed"),
            }
        except:
            overview["experiments"] = {"total": 0}

    # Pipelines
    if "pipeline_builder" in skills:
        try:
            pipe = skills["pipeline_builder"]
            pipes = pipe.data.get("pipelines", {})
            overview["pipelines"] = {"total": len(pipes)}
        except:
            overview["pipelines"] = {"total": 0}

    # Server management
    if "hetzner_server" in skills:
        try:
            hetzner = skills["hetzner_server"]
            servers_data = hetzner._get("/servers")
            servers = servers_data.get("servers", [])
            overview["servers"] = {
                "total": len(servers),
                "running": sum(1 for s in servers if s.get("status") == "running"),
            }
        except:
            overview["servers"] = {"total": 0}

    return jsonify(overview)


@app.route("/api/dashboard/skills")
def dashboard_skills():
    """List all skills with status."""
    api = get_api()
    skills_info = []
    for name, skill in api._skills.items():
        info = {
            "name": name,
            "class": skill.__class__.__name__,
            "available": True,
        }
        skills_info.append(info)
    return jsonify({"skills": skills_info, "total": len(skills_info)})


@app.route("/api/dashboard/models")
def dashboard_models():
    """Model registry data."""
    api = get_api()
    if "model_registry" not in api._skills:
        return jsonify({"models": [], "deployed": {}})
    reg = api._skills["model_registry"]
    return jsonify({
        "models": list(reg.registry.get("models", {}).values()),
        "deployed": reg.registry.get("deployed", {}),
    })


@app.route("/api/dashboard/experiments")
def dashboard_experiments():
    """Experiment tracker data."""
    api = get_api()
    if "experiment_tracker" not in api._skills:
        return jsonify({"experiments": []})
    exp = api._skills["experiment_tracker"]
    return jsonify({"experiments": list(exp.data.get("experiments", {}).values())})


@app.route("/api/dashboard/pipelines")
def dashboard_pipelines():
    """Pipeline builder data."""
    api = get_api()
    if "pipeline_builder" not in api._skills:
        return jsonify({"pipelines": []})
    pipe = api._skills["pipeline_builder"]
    return jsonify({"pipelines": list(pipe.data.get("pipelines", {}).values())})


@app.route("/api/dashboard/evaluations")
def dashboard_evaluations():
    """Evaluation history."""
    api = get_api()
    if "evaluation" not in api._skills:
        return jsonify({"evaluations": []})
    eval_skill = api._skills["evaluation"]
    return jsonify({"evaluations": eval_skill.data.get("evaluations", [])})


@app.route("/api/dashboard/servers")
def dashboard_servers():
    """Hetzner servers."""
    api = get_api()
    if "hetzner_server" not in api._skills:
        return jsonify({"servers": []})
    hetzner = api._skills["hetzner_server"]
    data = hetzner._get("/servers")
    return jsonify({"servers": data.get("servers", [])})


@app.route("/api/dashboard/voice")
def dashboard_voice():
    """Voice assistant status."""
    api = get_api()
    if "voice_assistant" not in api._skills:
        return jsonify({"status": {"tts_engine": "none", "listening": False}})
    va = api._skills["voice_assistant"]
    return jsonify({"status": va.get_status()})


@app.route("/api/dashboard/devices")
def dashboard_devices():
    """Connected devices."""
    api = get_api()
    if "device_manager" not in api._skills:
        return jsonify({"devices": []})
    dm = api._skills["device_manager"]
    return jsonify({"devices": list(dm.data.get("devices", {}).values())})


def run_dashboard(host="0.0.0.0", port=5000):
    """Run the dashboard server."""
    print(f"📊 EvolvixOS Dashboard starting on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_dashboard()
