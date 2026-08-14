"""
EvolvixOS Voice Gateway
Local voice interface gateway providing STT, Agent core integration, TTS, session management, and authentication.
"""

from voice_gateway.config import VoiceGatewayConfig
from voice_gateway.session_manager import VoiceSessionManager
from voice_gateway.auth import validate_api_key, require_api_key
from voice_gateway.audio_utils import convert_to_wav, is_valid_wav, get_audio_info
from voice_gateway.gateway import voice_gateway_bp

__all__ = [
    "VoiceGatewayConfig",
    "VoiceSessionManager",
    "validate_api_key",
    "require_api_key",
    "convert_to_wav",
    "is_valid_wav",
    "get_audio_info",
    "voice_gateway_bp",
]
