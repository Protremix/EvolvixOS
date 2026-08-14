"""
EvolvixOS — Main Entry Point v0.3
100% local, zero tokens, zero external API calls.
Learns from ALL open-source skills on GitHub.

Modes:
  python main.py                          → Interactive CLI mode
  python main.py "do something"           → Single task
  python main.py --web                    → Web UI (port 5000)
  python main.py --api                    → API server for external projects (port 5001)
  python main.py --api --web              → Both API and Web UI
  python main.py --voice                  → Voice interaction mode
  python main.py --project /path/to/code  → Load and analyze a project
  python main.py --discover               → Search GitHub for new AI skills
  python main.py --discover --auto        → Full auto: discover → install → learn
  python main.py --catalog                → Show GitHub skill catalog
"""

import sys
import argparse
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(
        description="EvolvixOS v0.3 — 100% local AI agent. Zero tokens. Learns from GitHub."
    )
    parser.add_argument("task", nargs="?", help="Task to execute")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    parser.add_argument("--web", action="store_true", help="Start web UI on port 5000")
    parser.add_argument("--api", action="store_true", help="Start API server on port 5001")
    parser.add_argument("--voice", action="store_true", help="Voice interaction mode")
    parser.add_argument("--project", action="store_true", help="Load and analyze a project")
    parser.add_argument("--discover", action="store_true", help="Search GitHub for new AI skills")
    parser.add_argument("--auto", action="store_true", help="Full auto-discovery: discover → install → learn")
    parser.add_argument("--catalog", action="store_true", help="Show GitHub skill catalog")
    parser.add_argument("--model", default=None, help="Override primary model")
    parser.add_argument("--port", type=int, default=None, help="Override port")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # === GITHUB DISCOVERY MODE ===
    if args.discover:
        from skills.github_discovery.skill import GitHubSkillDiscovery
        discovery = GitHubSkillDiscovery(config={"skills_dir": "./skills", "cache_dir": "./data/github_cache"})

        if args.auto:
            print("🧬 Full auto-discovery: discover → install → learn")
            discovery.discover_all(min_stars=50)
            discovery.install_all_discovered(min_stars=100, max_install=20)
            discovery.learn_all_installed()
            discovery.get_skill_catalog()
            print(f"\n✅ Done! Discovered: {len(discovery.registry['discovered'])}, "
                  f"Installed: {len(discovery.registry['installed'])}, "
                  f"Learned: {len(discovery.registry['learned'])}")
        else:
            print("🔍 Discovering skills on GitHub...")
            discovery.discover_all(min_stars=50)
            discovery.get_skill_catalog()
        return

    if args.catalog:
        from skills.github_discovery.skill import GitHubSkillDiscovery
        discovery = GitHubSkillDiscovery(config={"skills_dir": "./skills", "cache_dir": "./data/github_cache"})
        discovery.get_skill_catalog()
        return

    # === API + WEB mode ===
    if args.api or args.web:
        threads = []

        if args.api:
            from api_server import EvolvixAPI
            api = EvolvixAPI(config_path=args.config)
            api_port = args.port or 5001

            def run_api():
                api.run(host="0.0.0.0", port=api_port)

            t = threading.Thread(target=run_api, daemon=True)
            t.start()
            threads.append(t)
            print(f"🧬 API server on http://localhost:{api_port}")

        if args.web:
            from web.app import create_app
            web_app = create_app(args.config)
            web_port = args.port or 5000

            def run_web():
                web_app.run(host="0.0.0.0", port=web_port)

            t = threading.Thread(target=run_web, daemon=True)
            t.start()
            threads.append(t)
            print(f"🌐 Web UI on http://localhost:{web_port}")

        print("\n🧬 EvolvixOS running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🧬 EvolvixOS shutting down.")
        return

    # === PROJECT ANALYSIS MODE ===
    if args.project and args.task:
        from skills.project_learner.skill import ProjectLearner
        learner = ProjectLearner(config={})

        print(f"📂 Loading project: {args.task}")
        result = learner.load_project(args.task)

        print(f"\n{'='*60}")
        print(f"Project: {result['name']}")
        print(f"Files: {result['file_count']}")
        print(f"Tech Stack: {', '.join(result['tech_stack'])}")
        print(f"\nDescription:")
        print(result['description'][:2000])
        print(f"\n{'='*60}")
        print(f"\nEvolvix now understands this project.")
        print(f"\nAsk questions about the project (type 'exit' to quit):")

        while True:
            try:
                question = input("\n❓ ")
                if question.lower().strip() in ["exit", "quit", "q"]:
                    break
                answer = learner.ask(result['name'], question)
                print(f"\n🧬 {answer}")
            except KeyboardInterrupt:
                break
        return

    # === VOICE MODE ===
    if args.voice:
        from skills.voice.skill import VoiceSkill
        import os

        voice = VoiceSkill(config={})

        print("🧬 EvolvixOS Voice Mode")
        print("   Speak into your microphone and Evolvix will respond.")
        print("   Type 'exit' to quit.\n")

        try:
            import sounddevice as sd
            import soundfile as sf
            import tempfile

            SAMPLE_RATE = 16000
            RECORD_SECONDS = 10

            while True:
                input("🎤 Press Enter to speak (or Ctrl+C to quit)...")

                print("🔴 Recording... (speak now)")
                audio = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
                sd.wait()
                print("⏹️  Processing...")

                temp_path = tempfile.mktemp(suffix=".wav")
                sf.write(temp_path, audio, SAMPLE_RATE)

                text = voice.speech_to_text(temp_path)
                os.unlink(temp_path)

                if not text.strip():
                    print("🧬 I didn't catch that. Try again.")
                    continue

                print(f"🗣️  You said: {text}")

                if text.lower().strip() in ["exit", "quit", "stop"]:
                    break

                from agent.core import AgentCore
                if 'agent' not in dir():
                    agent = AgentCore(config_path=args.config)
                response = agent.run(text)
                print(f"🧬 {response}")

                voice.text_to_speech(response[:500])

        except ImportError:
            print("⚠️  For voice mode, install: pip install sounddevice soundfile")
        return

    # === CLI MODE ===
    from agent.core import AgentCore
    agent = AgentCore(config_path=args.config)

    if args.model:
        agent.llm_config["primary_model"] = args.model

    if args.task:
        result = agent.run(args.task)
        print(f"\n{'='*60}\nResult:\n{result}\n{'='*60}")
    else:
        agent.chat()


if __name__ == "__main__":
    main()
