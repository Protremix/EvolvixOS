"""
Tests for EvolvixOS Voice Gateway.

Tests the /api/v1/voice/session endpoint and related session management endpoints.
All external dependencies (Whisper, AgentCore, Kokoro) are mocked.
"""

import io
import json
import os
import wave
from unittest.mock import MagicMock, patch

import pytest


# ─── 1. Sessions Endpoint Reachable ─────────────────────────────────

def test_voice_sessions_endpoint_reachable(client):
    """1. Test that the sessions listing endpoint responds."""
    response = client.get("/api/v1/voice/sessions")
    assert response.status_code == 200
    data = response.get_json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)


# ─── 2. Authentication ────────────────────────────────────────────────

def test_authentication_invalid_api_key(app, client, valid_wav_audio, mock_voice_skill, mock_agent_core):
    """2. Test that invalid API key is rejected when auth is enabled."""
    import voice_gateway.gateway as gw
    cfg = gw.get_gateway_config()
    # Enable auth via internal config dict
    cfg._gateway_config["auth_enabled"] = True
    cfg._gateway_config["api_key"] = "secret-key-456"
    os.environ["EVOLVIX_VOICE_API_KEY"] = "secret-key-456"

    mock_voice_skill.speech_to_text.return_value = "Hello"
    mock_agent_core.run.return_value = "Hi!"
    mock_voice_skill.text_to_speech.return_value = "/tmp/test.wav"

    try:
        # No API key provided
        res_no_key = client.post(
            "/api/v1/voice/session",
            data={"audio": (io.BytesIO(valid_wav_audio), "test.wav")},
            content_type="multipart/form-data",
        )
        assert res_no_key.status_code == 401

        # Wrong API key
        res_bad = client.post(
            "/api/v1/voice/session",
            data={"audio": (io.BytesIO(valid_wav_audio), "test.wav")},
            headers={"X-API-Key": "wrong-key"},
            content_type="multipart/form-data",
        )
        assert res_bad.status_code == 401

        # Correct API key
        res_good = client.post(
            "/api/v1/voice/session",
            data={"audio": (io.BytesIO(valid_wav_audio), "test.wav")},
            headers={"X-API-Key": "secret-key-456"},
            content_type="multipart/form-data",
        )
        assert res_good.status_code == 200
    finally:
        cfg._gateway_config["auth_enabled"] = False
        cfg._gateway_config["api_key"] = None
        os.environ.pop("EVOLVIX_VOICE_API_KEY", None)


# ─── 3. Valid Audio Upload ────────────────────────────────────────────

def test_audio_upload_valid_wav(client, valid_wav_audio, mock_voice_skill, mock_agent_core):
    """3. Test uploading a valid WAV audio file to /api/v1/voice/session."""
    mock_voice_skill.speech_to_text.return_value = "Hello Evolvix"
    mock_agent_core.run.return_value = "Hello! How can I help?"
    mock_voice_skill.text_to_speech.return_value = "/tmp/tts_output.wav"

    response = client.post(
        "/api/v1/voice/session",
        data={"audio": (io.BytesIO(valid_wav_audio), "speech.wav")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("transcript") == "Hello Evolvix"
    assert data.get("response") == "Hello! How can I help?"
    assert "session_id" in data
    assert "audio_url" in data


# ─── 4. Invalid Audio Format ─────────────────────────────────────────

def test_invalid_audio_format(client, invalid_audio):
    """4. Test error handling when uploading a non-WAV audio file."""
    response = client.post(
        "/api/v1/voice/session",
        data={"audio": (io.BytesIO(invalid_audio), "test.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


# ─── 5. Oversized Audio ──────────────────────────────────────────────

def test_oversized_audio(client, oversized_audio):
    """5. Test error handling when audio file exceeds 10MB."""
    response = client.post(
        "/api/v1/voice/session",
        data={"audio": (io.BytesIO(oversized_audio), "oversized.wav")},
        content_type="multipart/form-data",
    )
    assert response.status_code in (400, 413)
    data = response.get_json()
    assert "error" in data


# ─── 6. STT ──────────────────────────────────────────────────────────

def test_stt_transcription(client, valid_wav_audio, mock_voice_skill, mock_agent_core):
    """6. Test that Whisper STT is called and transcription is returned."""
    mock_voice_skill.speech_to_text.return_value = "Find me the best hotels in Barcelona"
    mock_agent_core.run.return_value = "I found several hotels."
    mock_voice_skill.text_to_speech.return_value = "/tmp/tts_output.wav"

    response = client.post(
        "/api/v1/voice/session",
        data={
            "audio": (io.BytesIO(valid_wav_audio), "speech.wav"),
            "language": "ru",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["transcript"] == "Find me the best hotels in Barcelona"
    mock_voice_skill.speech_to_text.assert_called_once()


# ─── 7. Chat Forwarding ──────────────────────────────────────────────

def test_chat_forwarding(client, valid_wav_audio, mock_voice_skill, mock_agent_core):
    """7. Test that transcribed text is forwarded to AgentCore."""
    mock_voice_skill.speech_to_text.return_value = "What is the weather?"
    mock_agent_core.run.return_value = "I cannot check weather right now."
    mock_voice_skill.text_to_speech.return_value = "/tmp/tts_output.wav"

    response = client.post(
        "/api/v1/voice/session",
        data={"audio": (io.BytesIO(valid_wav_audio), "speech.wav")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    mock_agent_core.run.assert_called_once()
    call_args = mock_agent_core.run.call_args
    assert "What is the weather?" in str(call_args)


# ─── 8. Session Continuity ───────────────────────────────────────────

def test_session_continuity(client, valid_wav_audio, mock_voice_skill, mock_agent_core):
    """8. Test that session_id preserves conversation context across requests."""
    mock_voice_skill.speech_to_text.side_effect = [
        "Find me a hotel in Barcelona",
        "Which one is the cheapest?",
    ]
    mock_agent_core.run.side_effect = [
        "I found several options.",
        "The cheapest one is Hotel XYZ.",
    ]
    mock_voice_skill.text_to_speech.return_value = "/tmp/tts_output.wav"

    # First request
    res1 = client.post(
        "/api/v1/voice/session",
        data={"audio": (io.BytesIO(valid_wav_audio), "speech.wav")},
        content_type="multipart/form-data",
    )
    assert res1.status_code == 200
    session_id = res1.get_json()["session_id"]

    # Second request with same session_id
    res2 = client.post(
        "/api/v1/voice/session",
        data={
            "audio": (io.BytesIO(valid_wav_audio), "speech.wav"),
            "session_id": session_id,
        },
        content_type="multipart/form-data",
    )
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2["session_id"] == session_id
    assert data2["transcript"] == "Which one is the cheapest?"
    assert data2["response"] == "The cheapest one is Hotel XYZ."

    # AgentCore should have been called with context from first exchange
    second_call_args = mock_agent_core.run.call_args_list[1]
    second_input = str(second_call_args)
    # The gateway prepends conversation history to the message
    assert "hotel" in second_input.lower() or "barcelona" in second_input.lower() or "previous" in second_input.lower()


# ─── 9. TTS ──────────────────────────────────────────────────────────

def test_tts_generation(client, valid_wav_audio, mock_voice_skill, mock_agent_core):
    """9. Test that TTS is called and audio_url is returned."""
    mock_voice_skill.speech_to_text.return_value = "Hello"
    mock_agent_core.run.return_value = "Hi there!"
    mock_voice_skill.text_to_speech.return_value = "/tmp/response_123.wav"

    response = client.post(
        "/api/v1/voice/session",
        data={"audio": (io.BytesIO(valid_wav_audio), "speech.wav")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "audio_url" in data
    assert "response_123.wav" in data["audio_url"]
    mock_voice_skill.text_to_speech.assert_called_once()


# ─── 10. Complete Voice Round Trip ────────────────────────────────────

def test_complete_voice_round_trip(client, valid_wav_audio, mock_voice_skill, mock_agent_core):
    """10. Full end-to-end: audio → STT → AgentCore → TTS → audio response."""
    mock_voice_skill.speech_to_text.return_value = "Turn on the lights"
    mock_agent_core.run.return_value = "Lights are now on."
    mock_voice_skill.text_to_speech.return_value = "/tmp/lights_on.wav"

    response = client.post(
        "/api/v1/voice/session",
        data={
            "audio": (io.BytesIO(valid_wav_audio), "command.wav"),
            "language": "en",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["transcript"] == "Turn on the lights"
    assert data["response"] == "Lights are now on."
    assert "audio_url" in data
    assert "session_id" in data
    assert "latency_ms" in data
    assert isinstance(data["latency_ms"], (int, float))
    assert data["latency_ms"] > 0


# ─── 11. Timeout Handling ─────────────────────────────────────────────

def test_timeout_handling(client, valid_wav_audio, mock_voice_skill):
    """11. Test handling when STT service times out."""
    mock_voice_skill.speech_to_text.side_effect = TimeoutError("Whisper timed out")

    response = client.post(
        "/api/v1/voice/session",
        data={"audio": (io.BytesIO(valid_wav_audio), "speech.wav")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


# ─── 12. Server Unavailable ──────────────────────────────────────────

def test_server_unavailable_handling(client, valid_wav_audio, mock_voice_skill, mock_agent_core):
    """12. Test handling when AgentCore is unreachable."""
    mock_voice_skill.speech_to_text.return_value = "Hello"
    mock_agent_core.run.side_effect = ConnectionError("Cannot connect to Ollama")

    response = client.post(
        "/api/v1/voice/session",
        data={"audio": (io.BytesIO(valid_wav_audio), "speech.wav")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


# ─── 13. Empty Speech ────────────────────────────────────────────────

def test_empty_speech_transcription(client, valid_wav_audio, mock_voice_skill):
    """13. Test handling when Whisper returns empty (silence)."""
    mock_voice_skill.speech_to_text.return_value = ""

    response = client.post(
        "/api/v1/voice/session",
        data={"audio": (io.BytesIO(valid_wav_audio), "silence.wav")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


# ─── 14. Session Creation and Listing ────────────────────────────────

def test_session_creation_and_listing(client, valid_wav_audio, mock_voice_skill, mock_agent_core):
    """14. Test creating a session and listing it."""
    mock_voice_skill.speech_to_text.return_value = "Hello"
    mock_agent_core.run.return_value = "Hi!"
    mock_voice_skill.text_to_speech.return_value = "/tmp/test.wav"

    # Create a session via voice endpoint
    res = client.post(
        "/api/v1/voice/session",
        data={"audio": (io.BytesIO(valid_wav_audio), "speech.wav")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    session_id = res.get_json()["session_id"]

    # List sessions
    list_res = client.get("/api/v1/voice/sessions")
    assert list_res.status_code == 200
    sessions = list_res.get_json()["sessions"]
    assert any(s["session_id"] == session_id for s in sessions)


# ─── 15. Session Deletion ────────────────────────────────────────────

def test_session_deletion(client, valid_wav_audio, mock_voice_skill, mock_agent_core):
    """15. Test deleting a session."""
    mock_voice_skill.speech_to_text.return_value = "Hello"
    mock_agent_core.run.return_value = "Hi!"
    mock_voice_skill.text_to_speech.return_value = "/tmp/test.wav"

    # Create session
    res = client.post(
        "/api/v1/voice/session",
        data={"audio": (io.BytesIO(valid_wav_audio), "speech.wav")},
        content_type="multipart/form-data",
    )
    session_id = res.get_json()["session_id"]

    # Verify session exists
    get_res = client.get(f"/api/v1/voice/session/{session_id}")
    assert get_res.status_code == 200

    # Delete session
    del_res = client.delete(f"/api/v1/voice/session/{session_id}")
    assert del_res.status_code == 200

    # Verify session is gone
    get_res2 = client.get(f"/api/v1/voice/session/{session_id}")
    assert get_res2.status_code == 404

    # Attempt duplicate delete
    del_again = client.delete(f"/api/v1/voice/session/{session_id}")
    assert del_again.status_code == 404
