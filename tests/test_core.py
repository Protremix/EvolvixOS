"""
EvolvixOS — Tests
Basic tests for the core system. Run with: pytest tests/
"""

import os
import sys
import json
import yaml
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestProjectStructure:
    """Test that the project has all required files."""

    REQUIRED_FILES = [
        "main.py", "api_server.py", "evolvix_client.py",
        "discover_skills.py", "setup.sh", "requirements.txt",
        "README.md", "CONTRIBUTING.md", "ARCHITECTURE.md", "LICENSE",
        "Dockerfile", "docker-compose.yml",
        "agent/core.py", "agent/memory.py", "agent/planner.py",
        "config/config.yaml",
    ]

    @pytest.mark.parametrize("file_path", REQUIRED_FILES)
    def test_file_exists(self, file_path):
        assert (PROJECT_ROOT / file_path).exists(), f"Missing: {file_path}"


class TestConfig:
    """Test configuration file."""

    @pytest.fixture
    def config(self):
        with open(PROJECT_ROOT / "config" / "config.yaml") as f:
            return yaml.safe_load(f)["config"]

    def test_has_llm_config(self, config):
        assert "llm" in config
        assert "primary_model" in config["llm"]
        assert "host" in config["llm"]

    def test_has_skills_config(self, config):
        assert "skills" in config

    def test_uses_ollama(self, config):
        assert "ollama" in config["llm"]["host"] or "localhost" in config["llm"]["host"]

    def test_has_github_discovery(self, config):
        assert "github_discovery" in config["skills"]

    def test_has_api_config(self, config):
        assert "api" in config
        assert "port" in config["api"]


class TestSkills:
    """Test that skills exist and follow the interface."""

    EXPECTED_SKILLS = [
        "research", "coding", "video", "audio", "image",
        "voice", "project_learner", "github_discovery", "deploy",
        "self_improver", "movie_maker",
    ]

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_exists(self, skill_name):
        skill_path = PROJECT_ROOT / "skills" / skill_name / "skill.py"
        assert skill_path.exists(), f"Missing skill: {skill_name}"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_has_class(self, skill_name):
        skill_path = PROJECT_ROOT / "skills" / skill_name / "skill.py"
        code = skill_path.read_text()
        has_class = "class Skill:" in code or any(l.strip().startswith("Skill = ") for l in code.splitlines())
        assert has_class, f"{skill_name} missing Skill class"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_has_run_method(self, skill_name):
        skill_path = PROJECT_ROOT / "skills" / skill_name / "skill.py"
        code = skill_path.read_text()
        assert "def run(self" in code, f"{skill_name} missing run() method"


class TestZeroTokens:
    """Verify the project is truly zero-token (no paid APIs)."""

    PAID_APIS = ["openai-api", "openai>=1", "openai==", "anthropic", "google-generativeai", "azure-ai", "replicate"]

    def test_no_paid_apis_in_requirements(self):
        req_path = PROJECT_ROOT / "requirements.txt"
        deps = req_path.read_text().lower()
        for api in self.PAID_APIS:
            assert api not in deps, f"Found paid API dependency: {api}"

    def test_config_uses_local_llm(self):
        config_path = PROJECT_ROOT / "config" / "config.yaml"
        config_text = config_path.read_text().lower()
        assert "ollama" in config_text or "localhost" in config_text


class TestClientSDK:
    """Test the client SDK has all expected methods."""

    @pytest.fixture
    def client_code(self):
        return (PROJECT_ROOT / "evolvix_client.py").read_text()

    def test_has_class(self, client_code):
        assert "class EvolvixClient" in client_code

    def test_has_chat(self, client_code):
        assert "def chat(" in client_code

    def test_has_voice(self, client_code):
        assert "def speech_to_text(" in client_code

    def test_has_project_loading(self, client_code):
        assert "def load_project(" in client_code

    def test_has_represent(self, client_code):
        assert "def represent(" in client_code


class TestDockerSetup:
    """Test Docker configuration."""

    def test_dockerfile_exists(self):
        assert (PROJECT_ROOT / "Dockerfile").exists()

    def test_docker_compose_exists(self):
        assert (PROJECT_ROOT / "docker-compose.yml").exists()

    def test_docker_compose_has_services(self):
        content = (PROJECT_ROOT / "docker-compose.yml").read_text()
        assert "evolvix" in content
        assert "searxng" in content


class TestClientSDKv2:
    """Test that the v2.0 Client SDK has all new endpoints."""

    @pytest.fixture
    def client_code(self):
        return (PROJECT_ROOT / "evolvix_client.py").read_text()

    @pytest.mark.parametrize("method", [
        "def status(", "def health(", "def chat(", "def chat_stream(",
        "def research(", "def code(", "def code_execute(", "def code_debug(",
        "def video(", "def get_video_status(", "def image(",
        "def text_to_speech(", "def music(", "def speech_to_text(",
        "def movie(", "def get_movie_status(",
        "def deploy(", "def discover(", "def discover_install(",
        "def discover_learned(", "def improve(", "def improve_skills(",
        "def load_project(", "def ask_project(", "def list_projects(",
        "def represent(", "def stop_representing(",
        "def search_memory(", "def docs(",
    ])
    def test_has_method(self, client_code, method):
        assert method in client_code, f"Client SDK missing method: {method}"

    # v0.4 new client methods
    @pytest.mark.parametrize("method", [
        "def scrape(", "def analyze_data(", "def data_chart(",
        "def read_document(", "def write_document(", "def convert_document(",
        "def translate(", "def translate_languages(", "def ocr(",
        "def edit_image(", "def process_audio(", "def edit_video(",
        "def analyze_code(", "def analyze_security(", "def summarize(",
        "def summarize_file(", "def convert_file(", "def scan_security(",
        "def scan_secrets(", "def math_solve(", "def create_chart(",
        "def schedule(", "def list_scheduled(", "def system_status(",
        "def system_processes(", "def send_email(", "def db_query(",
        "def db_execute(", "def build_markdown(", "def browser_navigate(",
        "def browser_screenshot(", "def browser_extract(", "def run_skill(",
    ])
    def test_has_v04_method(self, client_code, method):
        assert method in client_code, f"Client SDK missing v0.4 method: {method}"


class TestAPIServerv2:
    """Test that the v2.0 API server has all endpoints."""

    @pytest.fixture
    def api_code(self):
        return (PROJECT_ROOT / "api_server.py").read_text()

    @pytest.mark.parametrize("endpoint", [
        "/api/v1/status", "/api/v1/chat", "/api/v1/chat/stream",
        "/api/v1/research", "/api/v1/code", "/api/v1/code/execute",
        "/api/v1/code/debug", "/api/v1/video", "/api/v1/image",
        "/api/v1/audio/tts", "/api/v1/audio/music", "/api/v1/voice",
        "/api/v1/speak", "/api/v1/movie", "/api/v1/deploy",
        "/api/v1/discover", "/api/v1/discover/install", "/api/v1/discover/learned",
        "/api/v1/improve", "/api/v1/improve/skills",
        "/api/v1/project/load", "/api/v1/project/ask", "/api/v1/project/list",
        "/api/v1/project/represent", "/api/v1/memory", "/api/v1/docs",
        "/api/v1/health",
    ])
    def test_has_endpoint(self, api_code, endpoint):
        assert endpoint in api_code, f"API server missing endpoint: {endpoint}"

    # v0.4 new endpoints
    @pytest.mark.parametrize("endpoint", [
        "/api/v1/scrape", "/api/v1/data/analyze", "/api/v1/data/chart",
        "/api/v1/doc/read", "/api/v1/doc/write", "/api/v1/doc/convert",
        "/api/v1/translate", "/api/v1/translate/languages", "/api/v1/ocr",
        "/api/v1/image/edit", "/api/v1/audio/process", "/api/v1/video/edit",
        "/api/v1/analyze/code", "/api/v1/analyze/security",
        "/api/v1/summarize", "/api/v1/summarize/file", "/api/v1/convert",
        "/api/v1/scan/security", "/api/v1/scan/secrets", "/api/v1/math/solve",
        "/api/v1/chart", "/api/v1/schedule", "/api/v1/schedule/list",
        "/api/v1/system", "/api/v1/system/processes", "/api/v1/email/send",
        "/api/v1/db/query", "/api/v1/db/execute", "/api/v1/markdown",
        "/api/v1/browser/navigate", "/api/v1/browser/screenshot",
        "/api/v1/browser/extract", "/api/v1/skill/",
    ])
    def test_has_v04_endpoint(self, api_code, endpoint):
        assert endpoint in api_code, f"API server missing v0.4 endpoint: {endpoint}"
