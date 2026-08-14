import os
import sys
import io
import wave
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask

# Add repo directory to sys.path so voice_gateway can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from voice_gateway.gateway import voice_gateway_bp, init_voice_gateway
from voice_gateway.session_manager import VoiceSessionManager
from voice_gateway.config import VoiceGatewayConfig


def create_wav_bytes(duration_sec=0.1, sample_rate=16000, num_channels=1, sample_width=2):
    """Generate a valid WAV file in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        num_frames = int(sample_rate * duration_sec)
        wf.writeframes(b"\x00" * (num_frames * num_channels * sample_width))
    return buf.getvalue()


@pytest.fixture
def valid_wav_audio():
    """Fixture providing a valid 16kHz mono WAV file in bytes."""
    return create_wav_bytes(duration_sec=0.5, sample_rate=16000)


@pytest.fixture
def invalid_audio():
    """Fixture providing an invalid non-WAV audio file payload."""
    return b"THIS_IS_NOT_A_WAV_FILE_HEADER_PLAIN_TEXT_DATA_1234567890"


@pytest.fixture
def oversized_audio():
    """Fixture providing an oversized WAV file (>10MB)."""
    header = create_wav_bytes(duration_sec=0.01)
    extra_size = 10 * 1024 * 1024 + 1024  # 10MB + 1KB
    return header + (b"\x00" * extra_size)


@pytest.fixture
def mock_voice_skill():
    """Mock VoiceSkill for Speech-to-Text and Text-to-Speech."""
    skill = MagicMock()
    skill.speech_to_text.return_value = "Hello Evolvix"
    skill.text_to_speech.return_value = "/tmp/tts_output.wav"
    skill.list_voices.return_value = [
        {"id": "af", "name": "American Female", "lang": "en-US"},
        {"id": "am", "name": "American Male", "lang": "en-US"},
    ]
    return skill


@pytest.fixture
def mock_agent_core():
    """Mock AgentCore for conversation processing."""
    agent = MagicMock()
    agent.run.return_value = "I am EvolvixOS, your AI system."
    return agent


@pytest.fixture
def app(mock_voice_skill, mock_agent_core):
    """Flask application fixture with registered voice_gateway blueprint."""
    # Clear env vars that might interfere
    for key in ["EVOLVIX_VOICE_AUTH_ENABLED", "EVOLVIX_VOICE_API_KEY"]:
        os.environ.pop(key, None)

    # Reset singletons
    import voice_gateway.gateway as gw
    gw._config_instance = None
    gw._session_manager_instance = None
    gw._agent_instance = None
    gw._voice_skill_instance = None

    # Create a test config with auth disabled
    cfg = VoiceGatewayConfig()
    # Modify the internal config dict directly (properties are read-only)
    cfg._gateway_config["auth_enabled"] = False
    cfg._gateway_config["max_upload_mb"] = 10
    cfg._gateway_config["rate_limit"] = 100  # Higher for tests

    # Create a fresh session manager
    sm = VoiceSessionManager(timeout_minutes=30, max_messages=50)

    # Inject mocks
    init_voice_gateway(
        agent=mock_agent_core,
        voice_skill=mock_voice_skill,
        config=cfg,
        session_manager=sm,
    )

    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

    # Register without url_prefix — gateway already has full paths
    flask_app.register_blueprint(voice_gateway_bp)

    return flask_app


@pytest.fixture
def client(app):
    """Flask test client fixture."""
    return app.test_client()
