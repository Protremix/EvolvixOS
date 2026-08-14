"""
Voice Gateway Blueprint for EvolvixOS.

Provides REST endpoints for voice-based agent interactions:
  - POST   /api/v1/voice/session           (Process incoming speech, run agent, synthesize audio)
  - GET    /api/v1/voice/session/<id>       (Retrieve session details and history)
  - DELETE /api/v1/voice/session/<id>       (Clear session)
  - GET    /api/v1/voice/sessions           (List all active sessions)
"""

import collections
import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, jsonify, request, current_app

from voice_gateway.audio_utils import convert_to_wav, is_valid_wav, get_audio_info
from voice_gateway.auth import require_api_key, validate_api_key
from voice_gateway.config import VoiceGatewayConfig
from voice_gateway.session_manager import VoiceSessionManager

voice_gateway_bp = Blueprint("voice_gateway", __name__)

# Singletons for lazy loading or app-injected dependencies
_config_instance: Optional[VoiceGatewayConfig] = None
_session_manager_instance: Optional[VoiceSessionManager] = None
_agent_instance: Any = None
_voice_skill_instance: Any = None
_init_lock = threading.Lock()


class RateLimiter:
    """In-memory sliding window rate limiter per client IP."""

    def __init__(self, limit_per_minute: int = 30):
        self.limit = limit_per_minute
        self.requests: Dict[str, list] = collections.defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, ip: str, limit_override: Optional[int] = None) -> bool:
        limit = limit_override if limit_override is not None else self.limit
        with self.lock:
            now = time.time()
            cutoff = now - 60.0
            # Remove requests older than 1 minute
            self.requests[ip] = [t for t in self.requests[ip] if t > cutoff]
            if len(self.requests[ip]) >= limit:
                return False
            self.requests[ip].append(now)
            return True


_rate_limiter = RateLimiter(limit_per_minute=30)


def get_gateway_config() -> VoiceGatewayConfig:
    global _config_instance
    if _config_instance is None:
        with _init_lock:
            if _config_instance is None:
                _config_instance = VoiceGatewayConfig()
    return _config_instance


def get_session_manager() -> VoiceSessionManager:
    global _session_manager_instance
    if _session_manager_instance is None:
        with _init_lock:
            if _session_manager_instance is None:
                cfg = get_gateway_config()
                _session_manager_instance = VoiceSessionManager(
                    db_path="./data/voice_sessions.db",
                    timeout_minutes=cfg.session_timeout_min,
                    max_messages=50,
                )
    return _session_manager_instance


def get_agent_core():
    global _agent_instance
    if _agent_instance is None:
        with _init_lock:
            if _agent_instance is None:
                # Check if running within Flask app context with agent attached
                if current_app and hasattr(current_app, "agent"):
                    _agent_instance = current_app.agent
                else:
                    from agent.core import AgentCore
                    _agent_instance = AgentCore()
    return _agent_instance


def get_voice_skill():
    global _voice_skill_instance
    if _voice_skill_instance is None:
        with _init_lock:
            if _voice_skill_instance is None:
                # Check if running within Flask app context with voice skill attached
                if current_app and hasattr(current_app, "voice_skill"):
                    _voice_skill_instance = current_app.voice_skill
                elif current_app and hasattr(current_app, "_skills") and "voice" in current_app._skills:
                    _voice_skill_instance = current_app._skills["voice"]
                else:
                    from skills.voice.skill import VoiceSkill
                    cfg = get_gateway_config()
                    _voice_skill_instance = VoiceSkill(config={
                        "default_voice": cfg.default_tts_voice,
                        "sample_rate": 24000,
                        "output_dir": "./output/audio",
                    })
    return _voice_skill_instance


def init_voice_gateway(
    agent=None,
    voice_skill=None,
    config: Optional[VoiceGatewayConfig] = None,
    session_manager: Optional[VoiceSessionManager] = None,
):
    """
    Initialize or inject dependencies for the voice gateway.
    """
    global _agent_instance, _voice_skill_instance, _config_instance, _session_manager_instance
    with _init_lock:
        if config is not None:
            _config_instance = config
        if session_manager is not None:
            _session_manager_instance = session_manager
        if agent is not None:
            _agent_instance = agent
        if voice_skill is not None:
            _voice_skill_instance = voice_skill


# ===================================================================
# ROUTE HANDLERS
# ===================================================================

@voice_gateway_bp.route("/api/v1/voice/session", methods=["POST"])
def voice_session():
    """
    Process incoming voice audio stream from a Voice PE device, run the agent, and return TTS audio response.

    Form-data parameters:
      - audio (file): WAV audio file (16kHz, mono, 16-bit PCM expected)
      - session_id (string, optional): existing session ID for context continuity
      - language (string, optional): language code ('en', 'ru', etc.)
      - metadata (string, optional): JSON metadata string
    """
    start_time = time.time()
    cfg = get_gateway_config()

    # 1. Rate limiting check
    client_ip = request.remote_addr or "127.0.0.1"
    if not _rate_limiter.is_allowed(client_ip, cfg.rate_limit):
        return jsonify({
            "error": "Rate limit exceeded",
            "message": f"Maximum of {cfg.rate_limit} requests per minute allowed."
        }), 429

    # 2. Authentication check
    is_valid_auth, auth_err = validate_api_key(cfg)
    if not is_valid_auth:
        return jsonify({
            "error": "Unauthorized",
            "message": auth_err or "Authentication failed"
        }), 401

    # 3. Audio file existence and size check
    if "audio" not in request.files:
        return jsonify({
            "error": "Bad Request",
            "message": "Missing 'audio' file parameter in multipart form data."
        }), 400

    audio_file = request.files["audio"]
    if not audio_file or not audio_file.filename:
        return jsonify({
            "error": "Bad Request",
            "message": "Empty or invalid audio file provided."
        }), 400

    # Content length / size check
    audio_file.seek(0, os.SEEK_END)
    file_length = audio_file.tell()
    audio_file.seek(0)

    if file_length > cfg.max_upload_bytes:
        return jsonify({
            "error": "Payload Too Large",
            "message": f"Audio file size ({round(file_length / (1024 * 1024), 2)}MB) exceeds max upload limit of {cfg.max_upload_mb}MB."
        }), 413

    # Parse optional form parameters
    session_id = request.form.get("session_id", "").strip() or None
    language = request.form.get("language", "").strip() or cfg.default_language
    metadata_raw = request.form.get("metadata", "").strip()
    metadata = {}
    if metadata_raw:
        try:
            metadata = json.loads(metadata_raw)
        except Exception:
            pass

    session_mgr = get_session_manager()

    # Save audio upload to temporary file for processing
    temp_dir = Path("./output/temp_audio")
    temp_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(audio_file.filename).suffix or ".wav"
    temp_input_path = str(temp_dir / f"input_{int(time.time() * 1000)}_{os.getpid()}{suffix}")
    converted_path = None

    try:
        audio_file.save(temp_input_path)

        # Validate audio file format
        if not is_valid_wav(temp_input_path):
            return jsonify({
                "error": "Invalid audio file",
                "message": "Uploaded file is not a valid WAV audio file."
            }), 400

        # Convert audio to target format (16kHz, mono, 16-bit PCM) if needed
        converted_path = convert_to_wav(
            temp_input_path,
            target_sample_rate=16000,
            target_channels=1,
            target_sample_width=2
        )

        # 4. Speech-to-Text via VoiceSkill (Whisper)
        voice_skill = get_voice_skill()
        transcribed_text = voice_skill.speech_to_text(converted_path, language=language)

        if not transcribed_text or not transcribed_text.strip():
            return jsonify({
                "error": "Speech recognition failed",
                "message": "Could not transcribe audio into text or audio was silent."
            }), 400

        transcribed_text = transcribed_text.strip()

        # 5. Session Management & Continuity Context
        if not session_id:
            session_id = session_mgr.create_session(metadata=metadata)
        else:
            session_mgr.create_session(session_id=session_id, metadata=metadata)

        # Retrieve conversation history
        history = session_mgr.get_history(session_id)

        # Prepend history context if previous turns exist
        if history:
            context_turns = []
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                context_turns.append(f"{role}: {msg['content']}")
            context_str = "\n".join(context_turns)
            agent_input = (
                f"Previous conversation history for session:\n"
                f"{context_str}\n\n"
                f"Current User Message: {transcribed_text}"
            )
        else:
            agent_input = transcribed_text

        # 6. Execute Agent Core with user input (Timeout limit: 120s)
        agent = get_agent_core()
        agent_response = agent.run(agent_input)

        if not agent_response:
            agent_response = "I processed your request, but generated no output."

        # 7. Store user query and agent response in session history
        session_mgr.append_message(session_id, "user", transcribed_text)
        session_mgr.append_message(session_id, "assistant", str(agent_response))

        # 8. Text-to-Speech via VoiceSkill (Kokoro TTS)
        tts_voice = cfg.get_voice_for_language(language)
        out_audio_path = voice_skill.text_to_speech(str(agent_response), voice=tts_voice)

        # Construct public audio URL
        audio_filename = Path(out_audio_path).name if out_audio_path else ""
        audio_url = f"/api/v1/audio/file/{audio_filename}" if audio_filename else ""

        elapsed_ms = int((time.time() - start_time) * 1000)

        return jsonify({
            "session_id": session_id,
            "transcript": transcribed_text,
            "response": agent_response,
            "audio_url": audio_url,
            "latency_ms": elapsed_ms
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": f"Error processing voice request: {str(e)}"
        }), 500

    finally:
        # Clean up temporary uploaded audio files
        for p in [temp_input_path, converted_path]:
            if p and os.path.exists(p) and p != converted_path:
                try:
                    os.remove(p)
                except Exception:
                    pass


@voice_gateway_bp.route("/api/v1/voice/session/<session_id>", methods=["GET"])
def get_session_info(session_id: str):
    """
    Retrieve details and conversation history for a specific voice session.
    """
    cfg = get_gateway_config()
    is_valid_auth, auth_err = validate_api_key(cfg)
    if not is_valid_auth:
        return jsonify({
            "error": "Unauthorized",
            "message": auth_err or "Authentication failed"
        }), 401

    session_mgr = get_session_manager()
    session = session_mgr.get_session(session_id)

    if not session:
        return jsonify({
            "error": "Session not found",
            "message": f"Session ID '{session_id}' does not exist or has expired."
        }), 404

    return jsonify(session), 200


@voice_gateway_bp.route("/api/v1/voice/session/<session_id>", methods=["DELETE"])
def clear_session(session_id: str):
    """
    Clear/delete a specific voice session and its history.
    """
    cfg = get_gateway_config()
    is_valid_auth, auth_err = validate_api_key(cfg)
    if not is_valid_auth:
        return jsonify({
            "error": "Unauthorized",
            "message": auth_err or "Authentication failed"
        }), 401

    session_mgr = get_session_manager()
    removed = session_mgr.clear_session(session_id)

    if not removed:
        return jsonify({
            "error": "Session not found",
            "message": f"Session ID '{session_id}' not found or already removed."
        }), 404

    return jsonify({
        "status": "success",
        "message": f"Session '{session_id}' cleared successfully.",
        "session_id": session_id
    }), 200


@voice_gateway_bp.route("/api/v1/voice/sessions", methods=["GET"])
def list_active_sessions():
    """
    List all active voice sessions.
    """
    cfg = get_gateway_config()
    is_valid_auth, auth_err = validate_api_key(cfg)
    if not is_valid_auth:
        return jsonify({
            "error": "Unauthorized",
            "message": auth_err or "Authentication failed"
        }), 401

    session_mgr = get_session_manager()
    active_sessions = session_mgr.list_sessions()

    return jsonify({
        "sessions": active_sessions,
        "total": len(active_sessions)
    }), 200
