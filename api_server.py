"""
EvolvixOS — Unified API Server v2.0
One API. All capabilities. Zero cost. 100% local.

Every EvolvixOS skill is exposed as a REST endpoint.
External projects connect here and get a full AI agent for free.

Endpoints:
  === Core ===
  GET  /api/v1/status              → system status + all available skills
  POST /api/v1/chat                → chat with the agent (uses any skill automatically)
  POST /api/v1/chat/stream         → streaming chat (SSE)

  === Research ===
  POST /api/v1/research            → deep web research → report
  GET  /api/v1/research/{id}       → get research result

  === Coding ===
  POST /api/v1/code                → generate code
  POST /api/v1/code/execute        → generate + execute code
  POST /api/v1/code/debug          → debug existing code

  === Video ===
  POST /api/v1/video               → text-to-video generation
  GET  /api/v1/video/{id}           → get video generation status

  === Image ===
  POST /api/v1/image               → text-to-image generation

  === Audio ===
  POST /api/v1/audio/tts           → text-to-speech
  POST /api/v1/audio/music         → text-to-music generation
  POST /api/v1/voice               → speech-to-text (transcription)
  POST /api/v1/speak               → alias for /audio/tts

  === Movie ===
  POST /api/v1/movie               → full movie creation pipeline
  GET  /api/v1/movie/{id}          → get movie status

  === Deploy ===
  POST /api/v1/deploy              → deploy a project to a server via SSH

  === GitHub Discovery ===
  POST /api/v1/discover             → search GitHub for new skills to learn
  POST /api/v1/discover/install     → install a specific repo as a skill
  GET  /api/v1/discover/learned     → list all learned skills

  === Self-Improvement ===
  POST /api/v1/improve              → trigger self-improvement (write a new skill)
  GET  /api/v1/improve/skills       → list self-written skills

  === Project Learner ===
  POST /api/v1/project/load        → load a codebase for analysis
  POST /api/v1/project/ask         → ask about a loaded project
  GET  /api/v1/project/list         → list loaded projects
  POST /api/v1/project/represent    → assign Evolvix to represent a project

  === Memory ===
  GET  /api/v1/memory               → search agent memory

  === Management ===
  GET  /api/v1/docs                 → OpenAPI spec (auto-generated)
  GET  /api/v1/health               → health check

All endpoints are free. No API keys, no billing, no rate limits.
Your data never leaves your machine.
"""

import os
import sys
import json
import time
import uuid
import threading
import traceback
from pathlib import Path
from typing import Optional, Any

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import yaml

# Suppress verbose logs
import logging
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


class EvolvixAPI:
    """
    Unified REST API for EvolvixOS.
    One server, all skills, zero cost.
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        self.app = Flask(__name__)
        CORS(self.app)  # Any project can connect

        with open(config_path) as f:
            self.config = yaml.safe_load(f)["config"]

        self.app.config.update(self.config)

        # === Initialize Agent Core ===
        from agent.core import AgentCore
        self.agent = AgentCore(config_path=config_path)

        # === Initialize All Skills ===
        self._skills = {}
        self._init_skills()

        # === Job tracking (for async tasks like video/movie) ===
        self._jobs = {}
        self._lock = threading.Lock()

        # Active representation
        self.representing_project = None

        self._register_routes()

    def _init_skills(self):
        """Initialize all skill instances."""
        skills_config = self.config.get("skills", {})

        # Research
        try:
            from skills.research.skill import Skill as ResearchSkill
            self._skills["research"] = ResearchSkill(config=skills_config.get("research", {}))
        except Exception as e:
            print(f"  ⚠ Research skill: {e}")

        # Coding
        try:
            from skills.coding.skill import Skill as CodingSkill
            self._skills["coding"] = CodingSkill(config=skills_config.get("coding", {}))
        except Exception as e:
            print(f"  ⚠ Coding skill: {e}")

        # Video
        try:
            from skills.video.skill import Skill as VideoSkill
            self._skills["video"] = VideoSkill(config=skills_config.get("video", {}))
        except Exception as e:
            print(f"  ⚠ Video skill: {e}")

        # Image
        try:
            from skills.image.skill import Skill as ImageSkill
            self._skills["image"] = ImageSkill(config=skills_config.get("image", {}))
        except Exception as e:
            print(f"  ⚠ Image skill: {e}")

        # Audio
        try:
            from skills.audio.skill import Skill as AudioSkill
            self._skills["audio"] = AudioSkill(config=skills_config.get("audio", {}))
        except Exception as e:
            print(f"  ⚠ Audio skill: {e}")

        # Voice
        try:
            from skills.voice.skill import Skill as VoiceSkill
            self._skills["voice"] = VoiceSkill(config=skills_config.get("voice", {}))
        except Exception as e:
            print(f"  ⚠ Voice skill: {e}")

        # Deploy
        try:
            from skills.deploy.skill import Skill as DeploySkill
            self._skills["deploy"] = DeploySkill(config=skills_config.get("deploy", {}))
        except Exception as e:
            print(f"  ⚠ Deploy skill: {e}")

        # Project Learner
        try:
            from skills.project_learner.skill import Skill as ProjectLearner
            self._skills["project_learner"] = ProjectLearner(config=skills_config.get("project_learner", {}))
        except Exception as e:
            print(f"  ⚠ Project Learner: {e}")

        # GitHub Discovery
        try:
            from skills.github_discovery.skill import Skill as GitHubDiscovery
            self._skills["github_discovery"] = GitHubDiscovery(config=skills_config.get("github_discovery", {}))
        except Exception as e:
            print(f"  ⚠ GitHub Discovery: {e}")

        # Self-Improver
        try:
            from skills.self_improver.skill import Skill as SelfImprover
            self._skills["self_improver"] = SelfImprover(config=skills_config.get("self_improver", {}))
        except Exception as e:
            print(f"  ⚠ Self-Improver: {e}")

        # Movie Maker
        try:
            from skills.movie_maker.skill import Skill as MovieMaker
            self._skills["movie_maker"] = MovieMaker(config=skills_config.get("movie_maker", {}))
        except Exception as e:
            print(f"  ⚠ Movie Maker: {e}")

        # === v0.4 New Skills ===
        new_skill_map = {
            "web_scraper": ("skills.web_scraper.skill", "Skill"),
            "data_analyst": ("skills.data_analyst.skill", "Skill"),
            "document_processor": ("skills.document_processor.skill", "Skill"),
            "translator": ("skills.translator.skill", "Skill"),
            "ocr": ("skills.ocr.skill", "Skill"),
            "image_editor": ("skills.image_editor.skill", "Skill"),
            "audio_processor": ("skills.audio_processor.skill", "Skill"),
            "video_editor": ("skills.video_editor.skill", "Skill"),
            "code_analyzer": ("skills.code_analyzer.skill", "Skill"),
            "summarizer": ("skills.summarizer.skill", "Skill"),
            "file_converter": ("skills.file_converter.skill", "Skill"),
            "security_scanner": ("skills.security_scanner.skill", "Skill"),
            "math_solver": ("skills.math_solver.skill", "Skill"),
            "visualizer": ("skills.visualizer.skill", "Skill"),
            "scheduler": ("skills.scheduler.skill", "Skill"),
            "system_monitor": ("skills.system_monitor.skill", "Skill"),
            "email_sender": ("skills.email_sender.skill", "Skill"),
            "database_manager": ("skills.database_manager.skill", "Skill"),
            "markdown_builder": ("skills.markdown_builder.skill", "Skill"),
            "browser_automation": ("skills.browser_automation.skill", "Skill"),
        }
        for skill_name, (module_path, class_name) in new_skill_map.items():
            try:
                import importlib
                mod = importlib.import_module(f"skills.{skill_name}.skill")
                SkillClass = getattr(mod, class_name, None) or getattr(mod, skill_name.replace('_', ' ').title().replace(' ', ''), None)
                if SkillClass is None:
                    # Try common alias patterns
                    for attr in dir(mod):
                        obj = getattr(mod, attr)
                        if isinstance(obj, type) and hasattr(obj, 'run') and hasattr(obj, '__init__') and attr != 'Console':
                            SkillClass = obj
                            break
                if SkillClass:
                    self._skills[skill_name] = SkillClass(config=skills_config.get(skill_name, {}))
            except Exception as e:
                print(f"  ⚠ {skill_name}: {e}")



        # Device Connector — Connect to any device or app
        try:
            from skills.device_connector.skill import Skill as DeviceConnector
            self._skills["device_connector"] = DeviceConnector(config=skills_config.get("device_connector", {}))
        except Exception as e:
            print(f"  ⚠ Device Connector: {e}")

        # Genie — Zero-Code Natural Language Builder
        try:
            from skills.genie.skill import Skill as GenieSkill
            self._skills["genie"] = GenieSkill(config=skills_config.get("genie", {}))
        except Exception as e:
            print(f"  ⚠ Genie: {e}")

        # Hetzner server management
        try:
            from skills.hetzner_server.skill import Skill as HetznerSkill
            self._skills["hetzner_server"] = HetznerSkill(config=skills_config.get("hetzner_server", {}))
        except Exception as e:
            print(f"  ⚠ Hetzner: {e}")

        # Platform skills — AI Engineering Platform core
        platform_skills = {
            "model_registry": "skills.model_registry.skill",
            "experiment_tracker": "skills.experiment_tracker.skill",
            "pipeline_builder": "skills.pipeline_builder.skill",
            "model_server": "skills.model_server.skill",
            "evaluation": "skills.evaluation.skill",
        }
        for skill_name, module_path in platform_skills.items():
            try:
                import importlib
                mod = importlib.import_module(module_path)
                SkillClass = getattr(mod, "Skill", None)
                if SkillClass:
                    self._skills[skill_name] = SkillClass(config=skills_config.get(skill_name, {}))
            except Exception as e:
                print(f"  ⚠ {skill_name}: {e}")

        # Inject skills into pipeline builder
        if "pipeline_builder" in self._skills:
            self._skills["pipeline_builder"].set_skills(self._skills)

        # Voice assistant + Device manager
        try:
            from skills.voice_assistant.skill import Skill as VoiceSkill
            self._skills["voice_assistant"] = VoiceSkill(config=skills_config.get("voice_assistant", {}))
        except Exception as e:
            print(f"  ⚠ Voice: {e}")

        try:
            from skills.device_manager.skill import Skill as DeviceSkill
            self._skills["device_manager"] = DeviceSkill(config=skills_config.get("device_manager", {}))
        except Exception as e:
            print(f"  ⚠ Devices: {e}")

        print(f"  ✅ Loaded {len(self._skills)} skills: {', '.join(self._skills.keys())}")

    def _register_routes(self):
        app = self.app

        # ===================================================================
        # CORE
        # ===================================================================

        @app.route("/api/v1/health", methods=["GET"])
        def health():
            return jsonify({"status": "healthy", "timestamp": time.time()})

        @app.route("/api/v1/status", methods=["GET"])
        def status():
            """Full system status with all capabilities."""
            models = []
            try:
                import ollama
                client = ollama.Client(host=self.config["llm"]["host"])
                for m in client.list().get("models", []):
                    models.append({
                        "name": m.get("name", ""),
                        "size_gb": round(m.get("size", 0) / 1e9, 1),
                    })
            except Exception:
                pass

            return jsonify({
                "name": "EvolvixOS",
                "version": "2.1.0",
                "status": "online",
                "mode": "100% local, zero tokens, zero cost",
                "model": self.config["llm"]["primary_model"],
                "coder_model": self.config["llm"].get("coder_model", ""),
                "fast_model": self.config["llm"].get("fast_model", ""),
                "available_models": models,
                "skills_loaded": list(self._skills.keys()),
                "skills_count": len(self._skills),
                "projects_loaded": len(self._skills.get("project_learner", self._skills.get("project_learner", object)).projects) if hasattr(self._skills.get("project_learner", {}), "projects") else 0,
                "representing": self.representing_project,
                "active_jobs": len(self._jobs),
                "endpoints": self._all_endpoints(),
                "cost": "$0.00 — forever",
            })

        @app.route("/api/v1/chat", methods=["POST"])
        def chat():
            """Chat with the agent. It automatically selects the right skill."""
            data = request.json or {}
            message = data.get("message", "")
            session_id = data.get("session_id", str(uuid.uuid4()))
            project_context = data.get("project", None)
            use_voice = data.get("voice", False)

            if not message:
                return jsonify({"error": "No message provided"}), 400

            # Add project context if representing
            context_prefix = ""
            pl = self._skills.get("project_learner")
            if project_context and pl and hasattr(pl, "projects") and project_context in pl.projects:
                proj = pl.projects[project_context]
                context_prefix = f"You are representing the project '{proj['name']}'. "
                context_prefix += f"Description: {proj.get('description', 'N/A')}\n"
                context_prefix += f"Tech stack: {', '.join(proj.get('tech_stack', []))}\n\n"
            elif self.representing_project and pl and hasattr(pl, "projects") and self.representing_project in pl.projects:
                proj = pl.projects[self.representing_project]
                context_prefix = f"You are representing '{proj['name']}'.\n\n"

            full_message = context_prefix + message if context_prefix else message

            try:
                result = self.agent.run(full_message)
                response = {
                    "response": result,
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "project": project_context or self.representing_project,
                    "cost": "$0.00",
                }

                if use_voice:
                    try:
                        voice_skill = self._skills.get("voice")
                        if voice_skill:
                            audio_path = voice_skill.text_to_speech(result[:500])
                            response["audio_url"] = f"/api/v1/audio/file/{Path(audio_path).name}"
                    except Exception as e:
                        response["voice_error"] = str(e)

                return jsonify(response)
            except Exception as e:
                return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

        @app.route("/api/v1/chat/stream", methods=["POST"])
        def chat_stream():
            """Streaming chat via Server-Sent Events."""
            data = request.json or {}
            message = data.get("message", "")
            if not message:
                return jsonify({"error": "No message provided"}), 400

            def generate():
                try:
                    # Stream from Ollama directly for real-time output
                    import ollama
                    client = ollama.Client(host=self.config["llm"]["host"])
                    stream = client.chat(
                        model=self.config["llm"]["primary_model"],
                        messages=[{"role": "user", "content": message}],
                        stream=True,
                    )
                    for chunk in stream:
                        text = chunk.get("message", {}).get("content", "")
                        if text:
                            yield f"data: {json.dumps({'text': text})}\n\n"
                    yield f"data: {json.dumps({'done': True})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return Response(generate(), mimetype="text/event-stream")

        # ===================================================================
        # RESEARCH
        # ===================================================================

        @app.route("/api/v1/research", methods=["POST"])
        def research():
            """Deep web research → comprehensive report."""
            data = request.json or {}
            query = data.get("query", data.get("topic", ""))
            depth = data.get("depth", 5)
            max_words = data.get("max_words", 5000)

            if not query:
                return jsonify({"error": "No query provided"}), 400

            skill = self._skills.get("research")
            if not skill:
                return jsonify({"error": "Research skill not loaded"}), 503

            try:
                job_id = str(uuid.uuid4())
                result_container = {}

                def run_research():
                    try:
                        report = skill.run({
                            "query": query,
                            "depth": depth,
                            "max_words": max_words,
                        })
                        result_container["result"] = report
                        result_container["status"] = "completed"
                    except Exception as e:
                        result_container["error"] = str(e)
                        result_container["status"] = "failed"

                with self._lock:
                    self._jobs[job_id] = {
                        "type": "research",
                        "query": query,
                        "status": "running",
                        "started": time.time(),
                    }

                thread = threading.Thread(target=run_research)
                thread.start()
                thread.join(timeout=120)  # Wait up to 2 minutes

                with self._lock:
                    self._jobs[job_id]["status"] = result_container.get("status", "timeout")
                    self._jobs[job_id]["completed"] = time.time()

                if "result" in result_container:
                    return jsonify({
                        "job_id": job_id,
                        "query": query,
                        "report": result_container["result"],
                        "status": "completed",
                        "cost": "$0.00",
                    })
                else:
                    return jsonify({
                        "job_id": job_id,
                        "query": query,
                        "status": result_container.get("status", "timeout"),
                        "error": result_container.get("error", "Timed out"),
                    }), 504

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/research/<job_id>", methods=["GET"])
        def get_research(job_id):
            with self._lock:
                job = self._jobs.get(job_id)
            if not job:
                return jsonify({"error": "Job not found"}), 404
            return jsonify(job)

        # ===================================================================
        # CODING
        # ===================================================================

        @app.route("/api/v1/code", methods=["POST"])
        def code_generate():
            """Generate code from a natural language description."""
            data = request.json or {}
            prompt = data.get("prompt", data.get("description", ""))
            language = data.get("language", "python")
            execute = data.get("execute", False)

            if not prompt:
                return jsonify({"error": "No prompt provided"}), 400

            skill = self._skills.get("coding")
            if not skill:
                return jsonify({"error": "Coding skill not loaded"}), 503

            try:
                result = skill.run({
                    "action": "execute" if execute else "generate",
                    "prompt": prompt,
                    "language": language,
                })
                return jsonify({
                    "code": result,
                    "language": language,
                    "executed": execute,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/code/execute", methods=["POST"])
        def code_execute():
            """Generate and execute code."""
            data = request.json or {}
            prompt = data.get("prompt", "")
            language = data.get("language", "python")

            if not prompt:
                return jsonify({"error": "No prompt provided"}), 400

            skill = self._skills.get("coding")
            if not skill:
                return jsonify({"error": "Coding skill not loaded"}), 503

            try:
                result = skill.run({
                    "action": "execute",
                    "prompt": prompt,
                    "language": language,
                })
                return jsonify({
                    "result": result,
                    "language": language,
                    "executed": True,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/code/debug", methods=["POST"])
        def code_debug():
            """Debug existing code."""
            data = request.json or {}
            code = data.get("code", "")
            error = data.get("error", "")
            language = data.get("language", "python")

            if not code:
                return jsonify({"error": "No code provided"}), 400

            skill = self._skills.get("coding")
            if not skill:
                return jsonify({"error": "Coding skill not loaded"}), 503

            try:
                result = skill.run({
                    "action": "debug",
                    "code": code,
                    "error": error,
                    "language": language,
                })
                return jsonify({
                    "fixed_code": result,
                    "language": language,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # ===================================================================
        # VIDEO
        # ===================================================================

        @app.route("/api/v1/video", methods=["POST"])
        def video_generate():
            """Text-to-video generation."""
            data = request.json or {}
            prompt = data.get("prompt", "")
            duration = data.get("duration", 5)
            resolution = data.get("resolution", "720p")
            fps = data.get("fps", 24)

            if not prompt:
                return jsonify({"error": "No prompt provided"}), 400

            skill = self._skills.get("video")
            if not skill:
                return jsonify({"error": "Video skill not loaded"}), 503

            job_id = str(uuid.uuid4())

            def run_video():
                try:
                    with self._lock:
                        self._jobs[job_id]["status"] = "generating"

                    result = skill.run({
                        "prompt": prompt,
                        "duration": duration,
                        "resolution": resolution,
                        "fps": fps,
                    })

                    with self._lock:
                        self._jobs[job_id].update({
                            "status": "completed",
                            "result": result,
                            "completed": time.time(),
                        })
                except Exception as e:
                    with self._lock:
                        self._jobs[job_id].update({
                            "status": "failed",
                            "error": str(e),
                        })

            with self._lock:
                self._jobs[job_id] = {
                    "type": "video",
                    "prompt": prompt,
                    "status": "queued",
                    "started": time.time(),
                }

            thread = threading.Thread(target=run_video)
            thread.start()

            return jsonify({
                "job_id": job_id,
                "prompt": prompt,
                "status": "queued",
                "message": "Video generation started. Poll /api/v1/video/{job_id} for status.",
                "cost": "$0.00",
            }), 202

        @app.route("/api/v1/video/<job_id>", methods=["GET"])
        def video_status(job_id):
            with self._lock:
                job = self._jobs.get(job_id)
            if not job:
                return jsonify({"error": "Job not found"}), 404
            return jsonify(job)

        # ===================================================================
        # IMAGE
        # ===================================================================

        @app.route("/api/v1/image", methods=["POST"])
        def image_generate():
            """Text-to-image generation."""
            data = request.json or {}
            prompt = data.get("prompt", "")
            size = data.get("size", "1024x1024")

            if not prompt:
                return jsonify({"error": "No prompt provided"}), 400

            skill = self._skills.get("image")
            if not skill:
                return jsonify({"error": "Image skill not loaded"}), 503

            try:
                result = skill.run({
                    "prompt": prompt,
                    "size": size,
                })
                return jsonify({
                    "image_path": result if isinstance(result, str) else result.get("path", ""),
                    "prompt": prompt,
                    "size": size,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # ===================================================================
        # AUDIO
        # ===================================================================

        @app.route("/api/v1/audio/tts", methods=["POST"])
        def audio_tts():
            """Text-to-speech."""
            data = request.json or {}
            text = data.get("text", "")
            voice = data.get("voice", "af")

            if not text:
                return jsonify({"error": "No text provided"}), 400

            skill = self._skills.get("voice") or self._skills.get("audio")
            if not skill:
                return jsonify({"error": "Audio skill not loaded"}), 503

            try:
                audio_path = skill.text_to_speech(text, voice=voice)
                return send_file(str(audio_path), mimetype="audio/wav")
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/speak", methods=["POST"])
        def speak():
            """Alias for /audio/tts."""
            return audio_tts()

        @app.route("/api/v1/audio/music", methods=["POST"])
        def audio_music():
            """Text-to-music generation."""
            data = request.json or {}
            prompt = data.get("prompt", "")
            duration = data.get("duration", 10)

            if not prompt:
                return jsonify({"error": "No prompt provided"}), 400

            skill = self._skills.get("audio")
            if not skill:
                return jsonify({"error": "Audio skill not loaded"}), 503

            try:
                result = skill.run({
                    "action": "music",
                    "prompt": prompt,
                    "duration": duration,
                })
                return jsonify({
                    "music_path": result,
                    "prompt": prompt,
                    "duration": duration,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/voice", methods=["POST"])
        def voice_transcribe():
            """Speech-to-text (transcription)."""
            if "audio" not in request.files:
                return jsonify({"error": "No audio file provided"}), 400

            audio_file = request.files["audio"]
            temp_path = f"/tmp/evolvix_voice_{int(time.time())}.wav"
            audio_file.save(temp_path)

            skill = self._skills.get("voice")
            if not skill:
                os.unlink(temp_path)
                return jsonify({"error": "Voice skill not loaded"}), 503

            try:
                text = skill.speech_to_text(temp_path)
                os.unlink(temp_path)
                return jsonify({
                    "text": text,
                    "transcribed": True,
                    "cost": "$0.00",
                })
            except Exception as e:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/audio/file/<filename>", methods=["GET"])
        def serve_audio(filename):
            """Serve generated audio files."""
            audio_dir = Path(self.config.get("skills", {}).get("audio", {}).get("output_dir", "./output/audio"))
            filepath = audio_dir / filename
            if filepath.exists():
                return send_file(str(filepath), mimetype="audio/wav")
            return jsonify({"error": "Audio not found"}), 404

        # ===================================================================
        # MOVIE
        # ===================================================================

        @app.route("/api/v1/movie", methods=["POST"])
        def movie_create():
            """Full movie creation pipeline: script → images → voice → music → video."""
            data = request.json or {}
            prompt = data.get("prompt", data.get("topic", ""))
            style = data.get("style", "cinematic")
            voice = data.get("voice", "af")
            music = data.get("music", "epic")
            resolution = data.get("resolution", "720p")

            if not prompt:
                return jsonify({"error": "No prompt provided"}), 400

            skill = self._skills.get("movie_maker")
            if not skill:
                return jsonify({"error": "Movie Maker skill not loaded"}), 503

            job_id = str(uuid.uuid4())

            def run_movie():
                try:
                    with self._lock:
                        self._jobs[job_id]["status"] = "creating"
                        self._jobs[job_id]["progress"] = "Script generation..."

                    result = skill.run({
                        "prompt": prompt,
                        "style": style,
                        "voice": voice,
                        "music": music,
                        "resolution": resolution,
                    })

                    with self._lock:
                        self._jobs[job_id].update({
                            "status": "completed",
                            "result": result,
                            "completed": time.time(),
                        })
                except Exception as e:
                    with self._lock:
                        self._jobs[job_id].update({
                            "status": "failed",
                            "error": str(e),
                        })

            with self._lock:
                self._jobs[job_id] = {
                    "type": "movie",
                    "prompt": prompt,
                    "status": "queued",
                    "started": time.time(),
                }

            thread = threading.Thread(target=run_movie)
            thread.start()

            return jsonify({
                "job_id": job_id,
                "prompt": prompt,
                "status": "queued",
                "message": "Movie creation started. Poll /api/v1/movie/{job_id} for progress.",
                "cost": "$0.00",
            }), 202

        @app.route("/api/v1/movie/<job_id>", methods=["GET"])
        def movie_status(job_id):
            with self._lock:
                job = self._jobs.get(job_id)
            if not job:
                return jsonify({"error": "Job not found"}), 404
            return jsonify(job)

        # ===================================================================
        # DEPLOY
        # ===================================================================

        @app.route("/api/v1/deploy", methods=["POST"])
        def deploy():
            """Deploy a project to a server via SSH."""
            data = request.json or {}
            project_path = data.get("path", "")
            server = data.get("server", "")
            user = data.get("user", "")
            dest = data.get("destination", "/opt/app")
            ssh_key = data.get("ssh_key", None)

            if not project_path or not server:
                return jsonify({"error": "path and server are required"}), 400

            skill = self._skills.get("deploy")
            if not skill:
                return jsonify({"error": "Deploy skill not loaded"}), 503

            try:
                result = skill.run({
                    "action": "deploy",
                    "path": project_path,
                    "server": server,
                    "user": user,
                    "destination": dest,
                    "ssh_key": ssh_key,
                })
                return jsonify({
                    "deployed": True,
                    "server": server,
                    "destination": dest,
                    "result": result,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # ===================================================================
        # GITHUB DISCOVERY
        # ===================================================================

        @app.route("/api/v1/discover", methods=["POST"])
        def discover():
            """Search GitHub for new AI tools to learn from."""
            data = request.json or {}
            query = data.get("query", "")
            topic = data.get("topic", "")
            limit = data.get("limit", 20)
            auto_learn = data.get("auto_learn", True)

            skill = self._skills.get("github_discovery")
            if not skill:
                return jsonify({"error": "GitHub Discovery skill not loaded"}), 503

            try:
                result = skill.run({
                    "action": "search",
                    "query": query,
                    "topic": topic,
                    "limit": limit,
                    "auto_learn": auto_learn,
                })
                return jsonify({
                    "discovered": result,
                    "auto_learned": auto_learn,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/discover/install", methods=["POST"])
        def discover_install():
            """Install a specific GitHub repo as a skill."""
            data = request.json or {}
            repo_url = data.get("repo", data.get("url", ""))

            if not repo_url:
                return jsonify({"error": "No repo URL provided"}), 400

            skill = self._skills.get("github_discovery")
            if not skill:
                return jsonify({"error": "GitHub Discovery skill not loaded"}), 503

            try:
                result = skill.run({
                    "action": "install",
                    "repo": repo_url,
                })
                return jsonify({
                    "installed": True,
                    "repo": repo_url,
                    "result": result,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/discover/learned", methods=["GET"])
        def discover_learned():
            """List all skills learned from GitHub."""
            skill = self._skills.get("github_discovery")
            if not skill:
                return jsonify({"error": "GitHub Discovery skill not loaded"}), 503

            try:
                result = skill.run({"action": "list"})
                return jsonify({
                    "learned_skills": result,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # ===================================================================
        # SELF-IMPROVEMENT
        # ===================================================================

        @app.route("/api/v1/improve", methods=["POST"])
        def improve():
            """Trigger self-improvement — write a new skill for a task it can't do."""
            data = request.json or {}
            task = data.get("task", data.get("description", ""))

            if not task:
                return jsonify({"error": "No task provided"}), 400

            skill = self._skills.get("self_improver")
            if not skill:
                return jsonify({"error": "Self-Improver skill not loaded"}), 503

            try:
                result = skill.run({
                    "action": "create_skill",
                    "task": task,
                })
                return jsonify({
                    "improved": True,
                    "new_skill": result,
                    "message": "EvolvixOS wrote a new skill for itself!",
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/improve/skills", methods=["GET"])
        def improve_skills():
            """List all self-written skills."""
            skill = self._skills.get("self_improver")
            if not skill:
                return jsonify({"error": "Self-Improver skill not loaded"}), 503

            try:
                result = skill.run({"action": "list"})
                return jsonify({
                    "self_written_skills": result,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # ===================================================================
        # PROJECT LEARNER
        # ===================================================================

        @app.route("/api/v1/project/load", methods=["POST"])
        def project_load():
            """Load a codebase for analysis."""
            data = request.json or {}
            path = data.get("path", "")
            name = data.get("name", None)

            if not path or not os.path.exists(path):
                return jsonify({"error": f"Path not found: {path}"}), 400

            skill = self._skills.get("project_learner")
            if not skill:
                return jsonify({"error": "Project Learner skill not loaded"}), 503

            try:
                result = skill.run({
                    "action": "load",
                    "path": path,
                    "name": name,
                })
                return jsonify({
                    "status": "loaded",
                    "project": result,
                    "message": "Project loaded. Evolvix can now answer questions about it.",
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/project/ask", methods=["POST"])
        def project_ask():
            """Ask about a loaded project."""
            data = request.json or {}
            project_name = data.get("project", "")
            question = data.get("question", "")

            if not project_name or not question:
                return jsonify({"error": "project and question are required"}), 400

            skill = self._skills.get("project_learner")
            if not skill:
                return jsonify({"error": "Project Learner skill not loaded"}), 503

            try:
                answer = skill.run({
                    "action": "ask",
                    "project": project_name,
                    "question": question,
                })
                return jsonify({
                    "project": project_name,
                    "question": question,
                    "answer": answer,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/project/list", methods=["GET"])
        def project_list():
            """List all loaded projects."""
            skill = self._skills.get("project_learner")
            if not skill:
                return jsonify({"error": "Project Learner skill not loaded"}), 503

            try:
                result = skill.run({"action": "list"})
                return jsonify({
                    "projects": result,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/project/represent", methods=["POST"])
        def project_represent():
            """Make Evolvix represent a project."""
            data = request.json or {}
            project_name = data.get("project", "")

            skill = self._skills.get("project_learner")
            if not skill or not hasattr(skill, "projects"):
                return jsonify({"error": "Project Learner not loaded"}), 503

            if project_name not in skill.projects:
                return jsonify({"error": f"Project '{project_name}' not loaded. Load it first."}), 404

            self.representing_project = project_name
            return jsonify({
                "status": "representing",
                "project": project_name,
                "message": f"Evolvix is now representing '{project_name}'. All chat responses will include project context.",
                "cost": "$0.00",
            })

        @app.route("/api/v1/project/represent", methods=["DELETE"])
        def project_stop_representing():
            """Stop representing a project."""
            old = self.representing_project
            self.representing_project = None
            return jsonify({
                "status": "stopped",
                "was_representing": old,
                "cost": "$0.00",
            })

        # ===================================================================
        # v0.4 NEW SKILLS
        # ===================================================================

        # Generic skill runner — works for ALL skills
        @app.route("/api/v1/skill/<skill_name>", methods=["POST"])
        def run_skill_direct(skill_name):
            """Run any skill directly. Pass action + args."""
            if skill_name not in self._skills:
                return jsonify({"error": f"Skill '{skill_name}' not found. Available: {list(self._skills.keys())}"}), 404
            data = request.json or {}
            try:
                result = self._skills[skill_name].run(data)
                return jsonify({"skill": skill_name, "result": result, "cost": "$0.00"})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # --- Web Scraper ---
        @app.route("/api/v1/scrape", methods=["POST"])
        def scrape():
            data = request.json or {}
            skill = self._skills.get("web_scraper")
            if not skill:
                return jsonify({"error": "Web scraper skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Data Analyst ---
        @app.route("/api/v1/data/analyze", methods=["POST"])
        def data_analyze():
            data = request.json or {}
            skill = self._skills.get("data_analyst")
            if not skill:
                return jsonify({"error": "Data analyst skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/data/chart", methods=["POST"])
        def data_chart():
            data = request.json or {}
            data["action"] = "chart"
            skill = self._skills.get("data_analyst")
            if not skill:
                return jsonify({"error": "Data analyst skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Document Processor ---
        @app.route("/api/v1/doc/read", methods=["POST"])
        def doc_read():
            data = request.json or {}
            skill = self._skills.get("document_processor")
            if not skill:
                return jsonify({"error": "Document processor skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/doc/write", methods=["POST"])
        def doc_write():
            data = request.json or {}
            skill = self._skills.get("document_processor")
            if not skill:
                return jsonify({"error": "Document processor skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/doc/convert", methods=["POST"])
        def doc_convert():
            data = request.json or {}
            data["action"] = "convert"
            skill = self._skills.get("document_processor")
            if not skill:
                return jsonify({"error": "Document processor skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Translator ---
        @app.route("/api/v1/translate", methods=["POST"])
        def translate():
            data = request.json or {}
            data["action"] = "translate"
            skill = self._skills.get("translator")
            if not skill:
                return jsonify({"error": "Translator skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/translate/languages", methods=["GET"])
        def translate_languages():
            skill = self._skills.get("translator")
            if not skill:
                return jsonify({"error": "Translator skill not loaded"}), 404
            return jsonify({"languages": skill.run({"action": "list_languages"}), "cost": "$0.00"})

        # --- OCR ---
        @app.route("/api/v1/ocr", methods=["POST"])
        def ocr_extract():
            data = request.json or {}
            skill = self._skills.get("ocr")
            if not skill:
                return jsonify({"error": "OCR skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Image Editor ---
        @app.route("/api/v1/image/edit", methods=["POST"])
        def image_edit():
            data = request.json or {}
            skill = self._skills.get("image_editor")
            if not skill:
                return jsonify({"error": "Image editor skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Audio Processor ---
        @app.route("/api/v1/audio/process", methods=["POST"])
        def audio_process():
            data = request.json or {}
            skill = self._skills.get("audio_processor")
            if not skill:
                return jsonify({"error": "Audio processor skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Video Editor ---
        @app.route("/api/v1/video/edit", methods=["POST"])
        def video_edit():
            data = request.json or {}
            skill = self._skills.get("video_editor")
            if not skill:
                return jsonify({"error": "Video editor skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Code Analyzer ---
        @app.route("/api/v1/analyze/code", methods=["POST"])
        def analyze_code():
            data = request.json or {}
            skill = self._skills.get("code_analyzer")
            if not skill:
                return jsonify({"error": "Code analyzer skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/analyze/security", methods=["POST"])
        def analyze_security():
            data = request.json or {}
            data["action"] = "security"
            skill = self._skills.get("code_analyzer")
            if not skill:
                return jsonify({"error": "Code analyzer skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Summarizer ---
        @app.route("/api/v1/summarize", methods=["POST"])
        def summarize():
            data = request.json or {}
            skill = self._skills.get("summarizer")
            if not skill:
                return jsonify({"error": "Summarizer skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/summarize/file", methods=["POST"])
        def summarize_file():
            data = request.json or {}
            data["action"] = "summarize_file"
            skill = self._skills.get("summarizer")
            if not skill:
                return jsonify({"error": "Summarizer skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- File Converter ---
        @app.route("/api/v1/convert", methods=["POST"])
        def convert_file():
            data = request.json or {}
            data["action"] = "convert"
            skill = self._skills.get("file_converter")
            if not skill:
                return jsonify({"error": "File converter skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Security Scanner ---
        @app.route("/api/v1/scan/security", methods=["POST"])
        def scan_security():
            data = request.json or {}
            data["action"] = "scan"
            skill = self._skills.get("security_scanner")
            if not skill:
                return jsonify({"error": "Security scanner skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/scan/secrets", methods=["POST"])
        def scan_secrets():
            data = request.json or {}
            data["action"] = "find_secrets"
            skill = self._skills.get("security_scanner")
            if not skill:
                return jsonify({"error": "Security scanner skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Math Solver ---
        @app.route("/api/v1/math/solve", methods=["POST"])
        def math_solve():
            data = request.json or {}
            skill = self._skills.get("math_solver")
            if not skill:
                return jsonify({"error": "Math solver skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Visualizer ---
        @app.route("/api/v1/chart", methods=["POST"])
        def create_chart():
            data = request.json or {}
            skill = self._skills.get("visualizer")
            if not skill:
                return jsonify({"error": "Visualizer skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Scheduler ---
        @app.route("/api/v1/schedule", methods=["POST"])
        def schedule_task():
            data = request.json or {}
            skill = self._skills.get("scheduler")
            if not skill:
                return jsonify({"error": "Scheduler skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/schedule/list", methods=["GET"])
        def schedule_list():
            skill = self._skills.get("scheduler")
            if not skill:
                return jsonify({"error": "Scheduler skill not loaded"}), 404
            return jsonify({"jobs": skill.run({"action": "list"}), "cost": "$0.00"})

        # --- System Monitor ---
        @app.route("/api/v1/system", methods=["GET"])
        def system_overview():
            skill = self._skills.get("system_monitor")
            if not skill:
                return jsonify({"error": "System monitor skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": "overview"}), "cost": "$0.00"})

        @app.route("/api/v1/system/processes", methods=["GET"])
        def system_processes():
            skill = self._skills.get("system_monitor")
            if not skill:
                return jsonify({"error": "System monitor skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": "processes"}), "cost": "$0.00"})

        # --- Email Sender ---
        @app.route("/api/v1/email/send", methods=["POST"])
        def email_send():
            data = request.json or {}
            data["action"] = "send"
            skill = self._skills.get("email_sender")
            if not skill:
                return jsonify({"error": "Email sender skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Database Manager ---
        @app.route("/api/v1/db/query", methods=["POST"])
        def db_query():
            data = request.json or {}
            data["action"] = "query"
            skill = self._skills.get("database_manager")
            if not skill:
                return jsonify({"error": "Database manager skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/db/execute", methods=["POST"])
        def db_execute():
            data = request.json or {}
            data["action"] = "execute"
            skill = self._skills.get("database_manager")
            if not skill:
                return jsonify({"error": "Database manager skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Markdown Builder ---
        @app.route("/api/v1/markdown", methods=["POST"])
        def markdown_build():
            data = request.json or {}
            skill = self._skills.get("markdown_builder")
            if not skill:
                return jsonify({"error": "Markdown builder skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # --- Browser Automation ---
        @app.route("/api/v1/browser/navigate", methods=["POST"])
        def browser_navigate():
            data = request.json or {}
            data["action"] = "navigate"
            skill = self._skills.get("browser_automation")
            if not skill:
                return jsonify({"error": "Browser automation skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/browser/screenshot", methods=["POST"])
        def browser_screenshot():
            data = request.json or {}
            data["action"] = "screenshot"
            skill = self._skills.get("browser_automation")
            if not skill:
                return jsonify({"error": "Browser automation skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/browser/extract", methods=["POST"])
        def browser_extract():
            data = request.json or {}
            data["action"] = "get_text"
            skill = self._skills.get("browser_automation")
            if not skill:
                return jsonify({"error": "Browser automation skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # ===================================================================
        # HETZNER SERVER MANAGEMENT
        # ===================================================================

        @app.route("/api/v1/hetzner/servers", methods=["GET"])
        def hetzner_servers():
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": "list_servers"}), "cost": "$0.00"})

        @app.route("/api/v1/hetzner/servers", methods=["POST"])
        def hetzner_create_server():
            data = request.json or {}
            data["action"] = "create_server"
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/hetzner/servers/<int:server_id>", methods=["GET"])
        def hetzner_get_server(server_id):
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": "get_server", "server_id": server_id}), "cost": "$0.00"})

        @app.route("/api/v1/hetzner/servers/<int:server_id>", methods=["DELETE"])
        def hetzner_delete_server(server_id):
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": "delete_server", "server_id": server_id})})

        @app.route("/api/v1/hetzner/servers/<int:server_id>/power", methods=["POST"])
        def hetzner_power(server_id):
            data = request.json or {}
            action = data.get("action", "power_on")  # power_on, power_off, reboot, shutdown, reset
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": action, "server_id": server_id}), "cost": "$0.00"})

        @app.route("/api/v1/hetzner/deploy", methods=["POST"])
        def hetzner_deploy_evolvixos():
            data = request.json or {}
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            action = data.get("action", "deploy")
            if action == "create_new":
                return jsonify({"result": skill.run({
                    "action": "create_evolvixos_server",
                    "name": data.get("name", "evolvixos-prod"),
                    "server_type": data.get("server_type", "cpx42"),
                    "location": data.get("location", "hel1"),
                    "domain": data.get("domain", "evolvixos.com"),
                })})
            else:
                return jsonify({"result": skill.run({
                    "action": "deploy_evolvixos",
                    "server_id": data.get("server_id"),
                    "domain": data.get("domain", "evolvixos.com"),
                })})

        @app.route("/api/v1/hetzner/ssh-keys", methods=["GET"])
        def hetzner_ssh_keys():
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": "list_ssh_keys"}), "cost": "$0.00"})

        @app.route("/api/v1/hetzner/ssh-keys", methods=["POST"])
        def hetzner_add_ssh_key():
            data = request.json or {}
            data["action"] = "add_ssh_key"
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/hetzner/locations", methods=["GET"])
        def hetzner_locations():
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": "list_locations"}), "cost": "$0.00"})

        @app.route("/api/v1/hetzner/types", methods=["GET"])
        def hetzner_types():
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": "list_server_types"}), "cost": "$0.00"})

        @app.route("/api/v1/hetzner/estimate", methods=["GET"])
        def hetzner_estimate():
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": "estimate"}), "cost": "$0.00"})

        @app.route("/api/v1/hetzner/firewalls", methods=["GET"])
        def hetzner_firewalls():
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": "list_firewalls"}), "cost": "$0.00"})

        @app.route("/api/v1/hetzner/firewalls", methods=["POST"])
        def hetzner_create_firewall():
            data = request.json or {}
            data["action"] = "create_firewall"
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/hetzner/metrics/<int:server_id>", methods=["GET"])
        def hetzner_metrics(server_id):
            metric_type = request.args.get("type", "cpu")
            skill = self._skills.get("hetzner_server")
            if not skill:
                return jsonify({"error": "Hetzner skill not loaded"}), 404
            return jsonify({"result": skill.run({"action": "get_metrics", "server_id": server_id, "metric_type": metric_type}), "cost": "$0.00"})

        # ===================================================================
        # MODEL REGISTRY
        # ===================================================================

        @app.route("/api/v1/registry/models", methods=["GET"])
        def registry_list():
            skill = self._skills.get("model_registry")
            if not skill: return jsonify({"error": "Model registry not loaded"}), 404
            return jsonify({"result": skill.run({"action": "list"}), "cost": "$0.00"})

        @app.route("/api/v1/registry/models", methods=["POST"])
        def registry_register():
            data = request.json or {}
            data["action"] = "register"
            skill = self._skills.get("model_registry")
            if not skill: return jsonify({"error": "Model registry not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/registry/models/compare", methods=["POST"])
        def registry_compare():
            data = request.json or {}
            data["action"] = "compare"
            skill = self._skills.get("model_registry")
            if not skill: return jsonify({"error": "Model registry not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/registry/models/deploy", methods=["POST"])
        def registry_deploy():
            data = request.json or {}
            data["action"] = "deploy"
            skill = self._skills.get("model_registry")
            if not skill: return jsonify({"error": "Model registry not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/registry/models/deployed", methods=["GET"])
        def registry_deployed():
            skill = self._skills.get("model_registry")
            if not skill: return jsonify({"error": "Model registry not loaded"}), 404
            return jsonify({"result": skill.run({"action": "deployed"}), "cost": "$0.00"})

        # ===================================================================
        # EXPERIMENT TRACKER
        # ===================================================================

        @app.route("/api/v1/experiments", methods=["POST"])
        def exp_log():
            data = request.json or {}
            data["action"] = "log"
            skill = self._skills.get("experiment_tracker")
            if not skill: return jsonify({"error": "Experiment tracker not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/experiments", methods=["GET"])
        def exp_list():
            skill = self._skills.get("experiment_tracker")
            if not skill: return jsonify({"error": "Experiment tracker not loaded"}), 404
            params = {"action": "list"}
            if request.args.get("status"): params["status"] = request.args.get("status")
            return jsonify({"result": skill.run(params), "cost": "$0.00"})

        @app.route("/api/v1/experiments/compare", methods=["POST"])
        def exp_compare():
            data = request.json or {}
            data["action"] = "compare"
            skill = self._skills.get("experiment_tracker")
            if not skill: return jsonify({"error": "Experiment tracker not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/experiments/summary", methods=["GET"])
        def exp_summary():
            skill = self._skills.get("experiment_tracker")
            if not skill: return jsonify({"error": "Experiment tracker not loaded"}), 404
            return jsonify({"result": skill.run({"action": "summary"}), "cost": "$0.00"})

        @app.route("/api/v1/experiments/<exp_id>", methods=["GET"])
        def exp_get(exp_id):
            skill = self._skills.get("experiment_tracker")
            if not skill: return jsonify({"error": "Experiment tracker not loaded"}), 404
            return jsonify({"result": skill.run({"action": "get", "exp_id": exp_id}), "cost": "$0.00"})

        @app.route("/api/v1/experiments/<exp_id>", methods=["PATCH"])
        def exp_update(exp_id):
            data = request.json or {}
            data["action"] = "update"
            data["exp_id"] = exp_id
            skill = self._skills.get("experiment_tracker")
            if not skill: return jsonify({"error": "Experiment tracker not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # ===================================================================
        # PIPELINE BUILDER
        # ===================================================================

        @app.route("/api/v1/pipelines", methods=["POST"])
        def pipe_create():
            data = request.json or {}
            data["action"] = "create"
            skill = self._skills.get("pipeline_builder")
            if not skill: return jsonify({"error": "Pipeline builder not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/pipelines", methods=["GET"])
        def pipe_list():
            skill = self._skills.get("pipeline_builder")
            if not skill: return jsonify({"error": "Pipeline builder not loaded"}), 404
            return jsonify({"result": skill.run({"action": "list"}), "cost": "$0.00"})

        @app.route("/api/v1/pipelines/<pipe_id>", methods=["GET"])
        def pipe_get(pipe_id):
            skill = self._skills.get("pipeline_builder")
            if not skill: return jsonify({"error": "Pipeline builder not loaded"}), 404
            return jsonify({"result": skill.run({"action": "get", "pipe_id": pipe_id}), "cost": "$0.00"})

        @app.route("/api/v1/pipelines/<pipe_id>/run", methods=["POST"])
        def pipe_run(pipe_id):
            data = request.json or {}
            data["action"] = "run"
            data["pipe_id"] = pipe_id
            skill = self._skills.get("pipeline_builder")
            if not skill: return jsonify({"error": "Pipeline builder not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/pipelines/<pipe_id>", methods=["DELETE"])
        def pipe_delete(pipe_id):
            skill = self._skills.get("pipeline_builder")
            if not skill: return jsonify({"error": "Pipeline builder not loaded"}), 404
            return jsonify({"result": skill.run({"action": "delete", "pipe_id": pipe_id})})

        # ===================================================================
        # MODEL SERVER
        # ===================================================================

        @app.route("/api/v1/models/available", methods=["GET"])
        def models_available():
            skill = self._skills.get("model_server")
            if not skill: return jsonify({"error": "Model server not loaded"}), 404
            return jsonify({"result": skill.run({"action": "list_available"}), "cost": "$0.00"})

        @app.route("/api/v1/models/pull", methods=["POST"])
        def models_pull():
            data = request.json or {}
            data["action"] = "pull"
            skill = self._skills.get("model_server")
            if not skill: return jsonify({"error": "Model server not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/models/serve", methods=["POST"])
        def models_serve():
            data = request.json or {}
            data["action"] = "serve"
            skill = self._skills.get("model_server")
            if not skill: return jsonify({"error": "Model server not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/models/predict", methods=["POST"])
        def models_predict():
            data = request.json or {}
            data["action"] = "predict"
            skill = self._skills.get("model_server")
            if not skill: return jsonify({"error": "Model server not loaded"}), 404
            return jsonify(skill.run(data))

        @app.route("/api/v1/models/embed", methods=["POST"])
        def models_embed():
            data = request.json or {}
            data["action"] = "embed"
            skill = self._skills.get("model_server")
            if not skill: return jsonify({"error": "Model server not loaded"}), 404
            return jsonify(skill.run(data))

        @app.route("/api/v1/models/benchmark", methods=["POST"])
        def models_benchmark():
            data = request.json or {}
            data["action"] = "benchmark"
            skill = self._skills.get("model_server")
            if not skill: return jsonify({"error": "Model server not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/models/metrics", methods=["GET"])
        def models_metrics():
            skill = self._skills.get("model_server")
            if not skill: return jsonify({"error": "Model server not loaded"}), 404
            return jsonify({"result": skill.run({"action": "metrics"}), "cost": "$0.00"})

        # ===================================================================
        # EVALUATION FRAMEWORK
        # ===================================================================

        @app.route("/api/v1/evaluate", methods=["POST"])
        def eval_model():
            data = request.json or {}
            data["action"] = "evaluate"
            skill = self._skills.get("evaluation")
            if not skill: return jsonify({"error": "Evaluation framework not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/evaluate/compare", methods=["POST"])
        def eval_compare():
            data = request.json or {}
            data["action"] = "compare"
            skill = self._skills.get("evaluation")
            if not skill: return jsonify({"error": "Evaluation framework not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/evaluate/history", methods=["GET"])
        def eval_history():
            skill = self._skills.get("evaluation")
            if not skill: return jsonify({"error": "Evaluation framework not loaded"}), 404
            return jsonify({"result": skill.run({"action": "history"}), "cost": "$0.00"})

        # ===================================================================
        # VOICE ASSISTANT
        # ===================================================================

        @app.route("/api/v1/voice/speak", methods=["POST"])
        def voice_speak():
            data = request.json or {}
            data["action"] = "speak"
            skill = self._skills.get("voice_assistant")
            if not skill: return jsonify({"error": "Voice assistant not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/voice/listen", methods=["POST"])
        def voice_listen():
            data = request.json or {}
            data["action"] = "listen"
            skill = self._skills.get("voice_assistant")
            if not skill: return jsonify({"error": "Voice assistant not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/voice/converse", methods=["POST"])
        def voice_converse():
            data = request.json or {}
            data["action"] = "converse"
            skill = self._skills.get("voice_assistant")
            if not skill: return jsonify({"error": "Voice assistant not loaded"}), 404
            return jsonify(skill.run(data))

        @app.route("/api/v1/voice/status", methods=["GET"])
        def voice_status():
            skill = self._skills.get("voice_assistant")
            if not skill: return jsonify({"error": "Voice assistant not loaded"}), 404
            return jsonify(skill.run({"action": "status"}))

        @app.route("/api/v1/voice/voices", methods=["GET"])
        def voice_voices():
            skill = self._skills.get("voice_assistant")
            if not skill: return jsonify({"error": "Voice assistant not loaded"}), 404
            return jsonify({"result": skill.run({"action": "list_voices"}), "cost": "$0.00"})

        @app.route("/api/v1/voice/settings", methods=["POST"])
        def voice_settings():
            data = request.json or {}
            data["action"] = "set_voice"
            skill = self._skills.get("voice_assistant")
            if not skill: return jsonify({"error": "Voice assistant not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        # ===================================================================
        # DEVICE MANAGER
        # ===================================================================

        @app.route("/api/v1/devices/register", methods=["POST"])
        def device_register():
            data = request.json or {}
            data["action"] = "register"
            skill = self._skills.get("device_manager")
            if not skill: return jsonify({"error": "Device manager not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/devices", methods=["GET"])
        def device_list():
            skill = self._skills.get("device_manager")
            if not skill: return jsonify({"error": "Device manager not loaded"}), 404
            return jsonify({"result": skill.run({"action": "list"}), "cost": "$0.00"})

        @app.route("/api/v1/devices/<device_id>", methods=["GET"])
        def device_get(device_id):
            skill = self._skills.get("device_manager")
            if not skill: return jsonify({"error": "Device manager not loaded"}), 404
            return jsonify({"result": skill.run({"action": "get", "device_id": device_id}), "cost": "$0.00"})

        @app.route("/api/v1/devices/<device_id>/connect", methods=["POST"])
        def device_connect(device_id):
            skill = self._skills.get("device_manager")
            if not skill: return jsonify({"error": "Device manager not loaded"}), 404
            return jsonify({"result": skill.run({"action": "connect", "device_id": device_id}), "cost": "$0.00"})

        @app.route("/api/v1/devices/<device_id>/send", methods=["POST"])
        def device_send(device_id):
            data = request.json or {}
            data["action"] = "send"
            data["device_id"] = device_id
            skill = self._skills.get("device_manager")
            if not skill: return jsonify({"error": "Device manager not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/devices/broadcast", methods=["POST"])
        def device_broadcast():
            data = request.json or {}
            data["action"] = "broadcast"
            skill = self._skills.get("device_manager")
            if not skill: return jsonify({"error": "Device manager not loaded"}), 404
            return jsonify({"result": skill.run(data), "cost": "$0.00"})

        @app.route("/api/v1/devices/connect_info", methods=["GET"])
        def device_connect_info():
            skill = self._skills.get("device_manager")
            if not skill: return jsonify({"error": "Device manager not loaded"}), 404
            return jsonify({"result": skill.run({"action": "connect_info"}), "cost": "$0.00"})

        @app.route("/api/v1/devices/stats", methods=["GET"])
        def device_stats():
            skill = self._skills.get("device_manager")
            if not skill: return jsonify({"error": "Device manager not loaded"}), 404
            return jsonify({"result": skill.run({"action": "stats"}), "cost": "$0.00"})

        @app.route("/api/v1/devices/<device_id>", methods=["DELETE"])
        def device_delete(device_id):
            skill = self._skills.get("device_manager")
            if not skill: return jsonify({"error": "Device manager not loaded"}), 404
            return jsonify({"result": skill.run({"action": "delete", "device_id": device_id})})

        # ===================================================================
        # MEMORY
        # ===================================================================

        @app.route("/api/v1/memory", methods=["GET"])
        def memory_search():
            """Search agent's memory."""
            query = request.args.get("q", "")
            try:
                results = self.agent.memory.search(query) if hasattr(self.agent, "memory") else []
                return jsonify({
                    "query": query,
                    "results": results,
                    "cost": "$0.00",
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500


        # ===================================================================
        # TEMPLATES — 11,000+ website templates
        # ===================================================================

        @app.route("/api/v1/templates", methods=["GET"])
        def list_templates():
            """List all available templates (paginated)."""
            try:
                from skills.template_browser.skill import Skill as TemplateBrowser
                browser = TemplateBrowser()
                category = request.args.get("category", "")
                page = int(request.args.get("page", 1))
                per_page = int(request.args.get("per_page", 20))
                result = browser.run({"action": "list", "category": category, "page": page, "per_page": per_page})
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/templates/count", methods=["GET"])
        def template_count():
            """Get template counts by category."""
            try:
                from skills.template_browser.skill import Skill as TemplateBrowser
                browser = TemplateBrowser()
                return jsonify(browser.run({"action": "count"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/templates/categories", methods=["GET"])
        def template_categories():
            """List all template categories."""
            try:
                from skills.template_browser.skill import Skill as TemplateBrowser
                browser = TemplateBrowser()
                return jsonify(browser.run({"action": "categories"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/templates/search", methods=["GET"])
        def search_templates():
            """Search templates by name, tags, or category."""
            try:
                from skills.template_browser.skill import Skill as TemplateBrowser
                browser = TemplateBrowser()
                q = request.args.get("q", "")
                category = request.args.get("category", "")
                return jsonify(browser.run({"action": "search", "q": q, "category": category}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/templates/<path:template_path>", methods=["GET"])
        def get_template(template_path):
            """Get a specific template's HTML and metadata."""
            try:
                from skills.template_browser.skill import Skill as TemplateBrowser
                browser = TemplateBrowser()
                return jsonify(browser.run({"action": "get", "path": template_path}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/templates/render", methods=["POST"])
        def render_template():
            """Render a template with custom data."""
            try:
                from skills.template_browser.skill import Skill as TemplateBrowser
                browser = TemplateBrowser()
                data = request.json or {}
                return jsonify(browser.run({"action": "render", "path": data.get("path", ""), "data": data.get("data", {})}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500


        # ===================================================================
        # GENIE — Zero-Code Builder (just say what you need)
        # ===================================================================

        @app.route("/api/v1/genie", methods=["POST"])
        def genie_build():
            """Tell the Genie what you need. It builds everything for you."""
            try:
                data = request.json or {}
                request_text = data.get("request", "").strip()
                if not request_text:
                    return jsonify({"error": "Please tell me what you need. Example: 'I need a website for my bakery'"}), 400
                genie = self._skills.get("genie")
                if not genie:
                    from skills.genie.skill import Skill as GenieSkill
                    genie = GenieSkill()
                result = genie.run({"request": request_text})
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/genie/understand", methods=["POST"])
        def genie_understand():
            """Parse a natural language request and return the detected intent."""
            try:
                data = request.json or {}
                from skills.genie.skill import Genie
                g = Genie()
                intent = g._understand(data.get("request", ""))
                return jsonify({"intent": intent})
            except Exception as e:
                return jsonify({"error": str(e)}), 500


        # ===================================================================
        # DEVICE CONNECTOR — Control any device or app
        # ===================================================================

        @app.route("/api/v1/devices", methods=["GET"])
        def devices_list():
            dc = self._skills.get("device_connector")
            if not dc:
                from skills.device_connector.skill import Skill as DeviceConnector
                dc = DeviceConnector()
            return jsonify(dc.run({"action": "list"}))

        @app.route("/api/v1/devices/register", methods=["POST"])
        def devices_register():
            dc = self._skills.get("device_connector")
            if not dc:
                from skills.device_connector.skill import Skill as DeviceConnector
                dc = DeviceConnector()
            return jsonify(dc.run({**request.json, "action": "register"}))

        @app.route("/api/v1/devices/<device_id>/control", methods=["POST"])
        def devices_control(device_id):
            dc = self._skills.get("device_connector")
            if not dc:
                from skills.device_connector.skill import Skill as DeviceConnector
                dc = DeviceConnector()
            data = request.json or {}
            data["device_id"] = device_id
            data["action"] = "control"
            return jsonify(dc.run(data))

        @app.route("/api/v1/devices/<device_id>/status", methods=["GET"])
        def devices_status(device_id):
            dc = self._skills.get("device_connector")
            if not dc:
                from skills.device_connector.skill import Skill as DeviceConnector
                dc = DeviceConnector()
            return jsonify(dc.run({"action": "status", "device_id": device_id}))

        @app.route("/api/v1/devices/discover", methods=["GET"])
        def devices_discover():
            dc = self._skills.get("device_connector")
            if not dc:
                from skills.device_connector.skill import Skill as DeviceConnector
                dc = DeviceConnector()
            return jsonify(dc.run({"action": "discover"}))

        @app.route("/api/v1/devices/bridge", methods=["POST"])
        def devices_bridge():
            dc = self._skills.get("device_connector")
            if not dc:
                from skills.device_connector.skill import Skill as DeviceConnector
                dc = DeviceConnector()
            return jsonify(dc.run({**request.json, "action": "setup_bridge"}))

        @app.route("/api/v1/devices/<device_id>", methods=["DELETE"])
        def devices_remove(device_id):
            dc = self._skills.get("device_connector")
            if not dc:
                from skills.device_connector.skill import Skill as DeviceConnector
                dc = DeviceConnector()
            return jsonify(dc.run({"action": "remove", "device_id": device_id}))

        # ===================================================================
        # SUB-AGENTS — Spawn background AI workers
        # ===================================================================

        @app.route("/api/v1/agents/spawn", methods=["POST"])
        def agents_spawn():
            """Spawn a sub-agent to run a skill in the background."""
            try:
                from skills.sub_agents.skill import SubAgentManager
                mgr = SubAgentManager()
                data = request.json or {}
                agent_id = mgr.spawn(data.get("task_name", "task"), data.get("skill_name", ""), data.get("args", {}))
                return jsonify({"agent_id": agent_id, "status": "running"})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/agents/run", methods=["POST"])
        def agents_run():
            """Run multiple skills in parallel and return all results."""
            try:
                from skills.sub_agents.skill import SubAgentManager
                mgr = SubAgentManager()
                data = request.json or {}
                tasks = data.get("tasks", [])
                results = mgr.run_parallel(tasks)
                return jsonify({"results": results, "count": len(results)})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/agents", methods=["GET"])
        def agents_list():
            """List all active sub-agents."""
            try:
                from skills.sub_agents.skill import SubAgentManager
                mgr = SubAgentManager()
                return jsonify({"agents": mgr.list_active(), "count": len(mgr.list_active())})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/agents/<agent_id>", methods=["GET"])
        def agents_status(agent_id):
            """Get status of a specific sub-agent."""
            try:
                from skills.sub_agents.skill import SubAgentManager
                mgr = SubAgentManager()
                return jsonify(mgr.get_status(agent_id))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/agents/<agent_id>/result", methods=["GET"])
        def agents_result(agent_id):
            """Get result of a completed sub-agent."""
            try:
                from skills.sub_agents.skill import SubAgentManager
                mgr = SubAgentManager()
                return jsonify(mgr.get_result(agent_id))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/agents/<agent_id>", methods=["DELETE"])
        def agents_stop(agent_id):
            """Stop a running sub-agent."""
            try:
                from skills.sub_agents.skill import SubAgentManager
                mgr = SubAgentManager()
                mgr.stop(agent_id)
                return jsonify({"stopped": True, "agent_id": agent_id})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # ===================================================================
        # UNIVERSAL API MANAGER — Connect to any external API
        # ===================================================================

        @app.route("/api/v1/apis/register", methods=["POST"])
        def apis_register():
            """Register an external API for EvolvixOS to use."""
            try:
                from skills.api_manager.skill import Skill as ApiManager
                mgr = ApiManager()
                data = request.json or {}
                data["action"] = "register"
                return jsonify(mgr.run(data))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/apis", methods=["GET"])
        def apis_list():
            """List all registered APIs."""
            try:
                from skills.api_manager.skill import Skill as ApiManager
                mgr = ApiManager()
                return jsonify(mgr.run({"action": "list"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/apis/<api_name>/call", methods=["POST"])
        def apis_call(api_name):
            """Call an endpoint on a registered API."""
            try:
                from skills.api_manager.skill import Skill as ApiManager
                mgr = ApiManager()
                data = request.json or {}
                data["action"] = "call"
                data["name"] = api_name
                return jsonify(mgr.run(data))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/apis/<api_name>/health", methods=["GET"])
        def apis_health(api_name):
            """Check health of a registered API."""
            try:
                from skills.api_manager.skill import Skill as ApiManager
                mgr = ApiManager()
                return jsonify(mgr.run({"action": "health", "name": api_name}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/apis/chain", methods=["POST"])
        def apis_chain():
            """Chain multiple API calls together."""
            try:
                from skills.api_manager.skill import Skill as ApiManager
                mgr = ApiManager()
                data = request.json or {}
                data["action"] = "chain"
                return jsonify(mgr.run(data))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # ===================================================================
        # VOIP CALLS — Answer calls, send SMS, manage phone
        # ===================================================================

        @app.route("/api/v1/voip/setup", methods=["POST"])
        def voip_setup():
            """Set up VoIP provider (Twilio, Vonage, SIP)."""
            try:
                from skills.voip_calls.skill import Skill as VoipSkill
                skill = VoipSkill()
                data = request.json or {}
                data["action"] = "setup"
                return jsonify(skill.run(data))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/voip/call", methods=["POST"])
        def voip_call():
            """Make an outbound call."""
            try:
                from skills.voip_calls.skill import Skill as VoipSkill
                skill = VoipSkill()
                data = request.json or {}
                data["action"] = "call"
                return jsonify(skill.run(data))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/voip/answer", methods=["POST"])
        def voip_answer():
            """Answer an incoming call with AI voice."""
            try:
                from skills.voip_calls.skill import Skill as VoipSkill
                skill = VoipSkill()
                data = request.json or {}
                data["action"] = "answer"
                return jsonify(skill.run(data))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/voip/sms", methods=["POST"])
        def voip_sms():
            """Send an SMS via VoIP provider."""
            try:
                from skills.voip_calls.skill import Skill as VoipSkill
                skill = VoipSkill()
                data = request.json or {}
                data["action"] = "sms"
                return jsonify(skill.run(data))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/voip/voicemail", methods=["POST"])
        def voip_voicemail():
            """Transcribe voicemail."""
            try:
                from skills.voip_calls.skill import Skill as VoipSkill
                skill = VoipSkill()
                data = request.json or {}
                data["action"] = "voicemail"
                return jsonify(skill.run(data))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/voip/history", methods=["GET"])
        def voip_history():
            """Get call history."""
            try:
                from skills.voip_calls.skill import Skill as VoipSkill
                skill = VoipSkill()
                return jsonify(skill.run({"action": "history"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/voip/ivr", methods=["POST"])
        def voip_ivr():
            """Create an IVR menu."""
            try:
                from skills.voip_calls.skill import Skill as VoipSkill
                skill = VoipSkill()
                data = request.json or {}
                data["action"] = "ivr"
                return jsonify(skill.run(data))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # ===================================================================
        # LIFE MANAGER — Manage everything in real life
        # ===================================================================

        @app.route("/api/v1/life/tasks", methods=["GET", "POST"])
        def life_tasks():
            """Add or list tasks."""
            try:
                from skills.life_manager.skill import Skill as LifeSkill
                skill = LifeSkill()
                if request.method == "POST":
                    data = request.json or {}
                    data["action"] = "task_add"
                    return jsonify(skill.run(data))
                return jsonify(skill.run({"action": "task_list"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/life/tasks/<task_id>/complete", methods=["POST"])
        def life_task_complete(task_id):
            """Mark a task as complete."""
            try:
                from skills.life_manager.skill import Skill as LifeSkill
                skill = LifeSkill()
                return jsonify(skill.run({"action": "task_complete", "task_id": task_id}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/life/events", methods=["GET", "POST"])
        def life_events():
            """Add or list calendar events."""
            try:
                from skills.life_manager.skill import Skill as LifeSkill
                skill = LifeSkill()
                if request.method == "POST":
                    data = request.json or {}
                    data["action"] = "event_add"
                    return jsonify(skill.run(data))
                return jsonify(skill.run({"action": "event_list"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/life/contacts", methods=["GET", "POST"])
        def life_contacts():
            """Add or list contacts."""
            try:
                from skills.life_manager.skill import Skill as LifeSkill
                skill = LifeSkill()
                if request.method == "POST":
                    data = request.json or {}
                    data["action"] = "contact_add"
                    return jsonify(skill.run(data))
                return jsonify(skill.run({"action": "contact_list"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/life/expenses", methods=["GET", "POST"])
        def life_expenses():
            """Add or list expenses."""
            try:
                from skills.life_manager.skill import Skill as LifeSkill
                skill = LifeSkill()
                if request.method == "POST":
                    data = request.json or {}
                    data["action"] = "expense_add"
                    return jsonify(skill.run(data))
                return jsonify(skill.run({"action": "expense_list"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/life/goals", methods=["GET", "POST"])
        def life_goals():
            """Add or list goals."""
            try:
                from skills.life_manager.skill import Skill as LifeSkill
                skill = LifeSkill()
                if request.method == "POST":
                    data = request.json or {}
                    data["action"] = "goal_add"
                    return jsonify(skill.run(data))
                return jsonify(skill.run({"action": "goal_progress"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/life/shopping", methods=["GET", "POST"])
        def life_shopping():
            """Add or list shopping items."""
            try:
                from skills.life_manager.skill import Skill as LifeSkill
                skill = LifeSkill()
                if request.method == "POST":
                    data = request.json or {}
                    data["action"] = "shopping_add"
                    return jsonify(skill.run(data))
                return jsonify(skill.run({"action": "shopping_list"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/life/reminders", methods=["GET", "POST"])
        def life_reminders():
            """Add or list reminders."""
            try:
                from skills.life_manager.skill import Skill as LifeSkill
                skill = LifeSkill()
                if request.method == "POST":
                    data = request.json or {}
                    data["action"] = "reminder_add"
                    return jsonify(skill.run(data))
                return jsonify(skill.run({"action": "reminder_list"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/life/summary", methods=["GET"])
        def life_summary():
            """Get daily summary / morning briefing."""
            try:
                from skills.life_manager.skill import Skill as LifeSkill
                skill = LifeSkill()
                return jsonify(skill.run({"action": "summary"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/life/suggest", methods=["GET"])
        def life_suggest():
            """Get AI suggestions for what to do next."""
            try:
                from skills.life_manager.skill import Skill as LifeSkill
                skill = LifeSkill()
                return jsonify(skill.run({"action": "suggest"}))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # ===================================================================
        # DOCS / OPENAPI
        # ===================================================================

        @app.route("/api/v1/docs", methods=["GET"])
        def docs():
            """Auto-generated API documentation."""
            return jsonify(self._openapi_spec())

        @app.route("/", methods=["GET"])
        def root():
            """Root endpoint — welcome message with all endpoints."""
            return jsonify({
                "name": "EvolvixOS API",
                "version": "2.1.0",
                "tagline": "One API. All capabilities. Zero cost.",
                "docs": "/api/v1/docs",
                "status": "/api/v1/status",
                "health": "/api/v1/health",
                "endpoints": self._all_endpoints(),
                "cost": "$0.00 — forever",
            })

    def _all_endpoints(self) -> dict:
        """Return all available endpoints grouped by category."""
        return {
            "core": [
                "GET  /api/v1/status",
                "POST /api/v1/chat",
                "POST /api/v1/chat/stream",
                "GET  /api/v1/health",
            ],
            "research": [
                "POST /api/v1/research",
                "GET  /api/v1/research/{id}",
            ],
            "coding": [
                "POST /api/v1/code",
                "POST /api/v1/code/execute",
                "POST /api/v1/code/debug",
            ],
            "video": [
                "POST /api/v1/video",
                "GET  /api/v1/video/{id}",
                "POST /api/v1/video/edit",
            ],
            "image": [
                "POST /api/v1/image",
                "POST /api/v1/image/edit",
            ],
            "audio": [
                "POST /api/v1/audio/tts",
                "POST /api/v1/audio/music",
                "POST /api/v1/voice",
                "POST /api/v1/speak",
                "POST /api/v1/audio/process",
                "GET  /api/v1/audio/file/{filename}",
            ],
            "movie": [
                "POST /api/v1/movie",
                "GET  /api/v1/movie/{id}",
            ],
            "deploy": [
                "POST /api/v1/deploy",
            ],
            "github_discovery": [
                "POST /api/v1/discover",
                "POST /api/v1/discover/install",
                "GET  /api/v1/discover/learned",
            ],
            "self_improvement": [
                "POST /api/v1/improve",
                "GET  /api/v1/improve/skills",
            ],
            "project_learner": [
                "POST /api/v1/project/load",
                "POST /api/v1/project/ask",
                "GET  /api/v1/project/list",
                "POST /api/v1/project/represent",
                "DELETE /api/v1/project/represent",
            ],
            "web_scraper": [
                "POST /api/v1/scrape",
                "POST /api/v1/skill/web_scraper",
            ],
            "data_analyst": [
                "POST /api/v1/data/analyze",
                "POST /api/v1/data/chart",
            ],
            "document_processor": [
                "POST /api/v1/doc/read",
                "POST /api/v1/doc/write",
                "POST /api/v1/doc/convert",
            ],
            "translator": [
                "POST /api/v1/translate",
                "GET  /api/v1/translate/languages",
            ],
            "ocr": [
                "POST /api/v1/ocr",
            ],
            "image_editor": [
                "POST /api/v1/image/edit",
            ],
            "audio_processor": [
                "POST /api/v1/audio/process",
            ],
            "video_editor": [
                "POST /api/v1/video/edit",
            ],
            "code_analyzer": [
                "POST /api/v1/analyze/code",
                "POST /api/v1/analyze/security",
            ],
            "summarizer": [
                "POST /api/v1/summarize",
                "POST /api/v1/summarize/file",
            ],
            "file_converter": [
                "POST /api/v1/convert",
            ],
            "security_scanner": [
                "POST /api/v1/scan/security",
                "POST /api/v1/scan/secrets",
            ],
            "math_solver": [
                "POST /api/v1/math/solve",
            ],
            "visualizer": [
                "POST /api/v1/chart",
            ],
            "scheduler": [
                "POST /api/v1/schedule",
                "GET  /api/v1/schedule/list",
            ],
            "system_monitor": [
                "GET  /api/v1/system",
                "GET  /api/v1/system/processes",
            ],
            "email_sender": [
                "POST /api/v1/email/send",
            ],
            "database_manager": [
                "POST /api/v1/db/query",
                "POST /api/v1/db/execute",
            ],
            "markdown_builder": [
                "POST /api/v1/markdown",
            ],
            "browser_automation": [
                "POST /api/v1/browser/navigate",
                "POST /api/v1/browser/screenshot",
                "POST /api/v1/browser/extract",
            ],
            "generic_skill_runner": [
                "POST /api/v1/skill/{skill_name}",
            ],
            "hetzner": [
                "GET    /api/v1/hetzner/servers",
                "POST   /api/v1/hetzner/servers",
                "GET    /api/v1/hetzner/servers/{id}",
                "DELETE /api/v1/hetzner/servers/{id}",
                "POST   /api/v1/hetzner/servers/{id}/power",
                "POST   /api/v1/hetzner/deploy",
                "GET    /api/v1/hetzner/ssh-keys",
                "POST   /api/v1/hetzner/ssh-keys",
                "GET    /api/v1/hetzner/locations",
                "GET    /api/v1/hetzner/types",
                "GET    /api/v1/hetzner/estimate",
                "GET    /api/v1/hetzner/firewalls",
                "POST   /api/v1/hetzner/firewalls",
                "GET    /api/v1/hetzner/metrics/{id}",
            ],
            "model_registry": [
                "GET    /api/v1/registry/models",
                "POST   /api/v1/registry/models",
                "POST   /api/v1/registry/models/compare",
                "POST   /api/v1/registry/models/deploy",
                "GET    /api/v1/registry/models/deployed",
            ],
            "experiments": [
                "POST   /api/v1/experiments",
                "GET    /api/v1/experiments",
                "POST   /api/v1/experiments/compare",
                "GET    /api/v1/experiments/summary",
                "GET    /api/v1/experiments/{id}",
                "PATCH  /api/v1/experiments/{id}",
            ],
            "pipelines": [
                "POST   /api/v1/pipelines",
                "GET    /api/v1/pipelines",
                "GET    /api/v1/pipelines/{id}",
                "POST   /api/v1/pipelines/{id}/run",
                "DELETE /api/v1/pipelines/{id}",
            ],
            "model_server": [
                "GET    /api/v1/models/available",
                "POST   /api/v1/models/pull",
                "POST   /api/v1/models/serve",
                "POST   /api/v1/models/predict",
                "POST   /api/v1/models/embed",
                "POST   /api/v1/models/benchmark",
                "GET    /api/v1/models/metrics",
            ],
            "evaluation": [
                "POST   /api/v1/evaluate",
                "POST   /api/v1/evaluate/compare",
                "GET    /api/v1/evaluate/history",
            ],
            "voice": [
                "POST   /api/v1/voice/speak",
                "POST   /api/v1/voice/listen",
                "POST   /api/v1/voice/converse",
                "GET    /api/v1/voice/status",
                "GET    /api/v1/voice/voices",
                "POST   /api/v1/voice/settings",
            ],
            "devices": [
                "POST   /api/v1/devices/register",
                "GET    /api/v1/devices",
                "GET    /api/v1/devices/{id}",
                "POST   /api/v1/devices/{id}/connect",
                "POST   /api/v1/devices/{id}/send",
                "POST   /api/v1/devices/broadcast",
                "GET    /api/v1/devices/connect_info",
                "GET    /api/v1/devices/stats",
                "DELETE /api/v1/devices/{id}",
            ],
            "memory": [
                "GET  /api/v1/memory",
            ],
            "docs": [
                "GET  /api/v1/docs",
            ],
        }

    def _openapi_spec(self) -> dict:
        """Generate a basic OpenAPI spec."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "EvolvixOS API",
                "version": "2.1.0",
                "description": "One API. All capabilities. Zero cost. 100% local.",
                "license": {"name": "MIT"},
            },
            "servers": [
                {"url": f"http://localhost:{self.config.get('api', {}).get('port', 5001)}", "description": "Local"},
            ],
            "paths": {
                "/api/v1/chat": {
                    "post": {"summary": "Chat with the agent", "tags": ["core"]},
                },
                "/api/v1/research": {
                    "post": {"summary": "Deep web research", "tags": ["research"]},
                },
                "/api/v1/code": {
                    "post": {"summary": "Generate code", "tags": ["coding"]},
                },
                "/api/v1/code/execute": {
                    "post": {"summary": "Generate and execute code", "tags": ["coding"]},
                },
                "/api/v1/code/debug": {
                    "post": {"summary": "Debug code", "tags": ["coding"]},
                },
                "/api/v1/video": {
                    "post": {"summary": "Text-to-video", "tags": ["video"]},
                },
                "/api/v1/image": {
                    "post": {"summary": "Text-to-image", "tags": ["image"]},
                },
                "/api/v1/audio/tts": {
                    "post": {"summary": "Text-to-speech", "tags": ["audio"]},
                },
                "/api/v1/audio/music": {
                    "post": {"summary": "Text-to-music", "tags": ["audio"]},
                },
                "/api/v1/voice": {
                    "post": {"summary": "Speech-to-text", "tags": ["audio"]},
                },
                "/api/v1/movie": {
                    "post": {"summary": "Full movie creation pipeline", "tags": ["movie"]},
                },
                "/api/v1/deploy": {
                    "post": {"summary": "Deploy to server via SSH", "tags": ["deploy"]},
                },
                "/api/v1/discover": {
                    "post": {"summary": "Search GitHub for new skills", "tags": ["discovery"]},
                },
                "/api/v1/discover/install": {
                    "post": {"summary": "Install a repo as a skill", "tags": ["discovery"]},
                },
                "/api/v1/improve": {
                    "post": {"summary": "Self-improve (write new skill)", "tags": ["self-improvement"]},
                },
                "/api/v1/project/load": {
                    "post": {"summary": "Load a codebase for analysis", "tags": ["project"]},
                },
                "/api/v1/project/ask": {
                    "post": {"summary": "Ask about a project", "tags": ["project"]},
                },
                "/api/v1/status": {
                    "get": {"summary": "System status", "tags": ["core"]},
                },
                "/api/v1/memory": {
                    "get": {"summary": "Search agent memory", "tags": ["memory"]},
                },
                "/api/v1/templates": {
                    "method": "GET",
                    "description": "List 11,000+ website templates (paginated, filter by category)"
                },
                "/api/v1/templates/count": {
                    "method": "GET",
                    "description": "Get template counts by category"
                },
                "/api/v1/templates/categories": {
                    "method": "GET",
                    "description": "List all template categories"
                },
                "/api/v1/templates/search?q=...": {
                    "method": "GET",
                    "description": "Search templates"
                },
                "/api/v1/templates/<path>": {
                    "method": "GET",
                    "description": "Get specific template HTML"
                },
                "/api/v1/templates/render": {
                    "method": "POST",
                    "description": "Render template with custom data"
                },
                "/api/v1/genie": {
                    "method": "POST",
                    "description": "Zero-code builder - say what you need, get a finished project"
                },
                "/api/v1/genie/understand": {
                    "method": "POST",
                    "description": "Parse a natural language request and detect intent"
                },
                "/api/v1/docs": {
                    "get": {"summary": "This documentation", "tags": ["docs"]},
                },
            },
        }

    def run(self, host=None, port=None):
        """Start the API server."""
        host = host or self.config.get("api", {}).get("host", "0.0.0.0")
        port = port or self.config.get("api", {}).get("port", 5001)

        print("\n" + "=" * 60)
        print("  🧬 EvolvixOS Unified API v2.1")
        print("  One API. All capabilities. Zero cost.")
        print("=" * 60)
        print(f"  Server:  http://{host}:{port}")
        print(f"  Skills:  {len(self._skills)} loaded")
        print(f"  Models:  {self.config['llm']['primary_model']}")
        print(f"  Cost:    $0.00 — forever")
        print("=" * 60)
        print(f"  Docs:    http://{host}:{port}/api/v1/docs")
        print(f"  Status:  http://{host}:{port}/api/v1/status")
        print("=" * 60 + "\n")

        self.app.run(host=host, port=port, debug=False, threaded=True)


# === ENTRY POINT ===
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="EvolvixOS Unified API Server")
    parser.add_argument("--host", default=None, help="Host to bind")
    parser.add_argument("--port", type=int, default=None, help="Port to bind")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    args = parser.parse_args()

    api = EvolvixAPI(config_path=args.config)
    api.run(host=args.host, port=args.port)
