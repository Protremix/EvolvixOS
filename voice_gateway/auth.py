"""
Authentication module for EvolvixOS Voice Gateway.

Provides API key validation against Authorization header, X-API-Key header, or ?api_key query parameter.
If no key is configured or auth is disabled, requests bypass authentication.
"""

from functools import wraps
from typing import Callable, Optional, Tuple
from flask import jsonify, request
from voice_gateway.config import VoiceGatewayConfig


def validate_api_key(config: VoiceGatewayConfig) -> Tuple[bool, Optional[str]]:
    """
    Validate incoming request credentials against configured API key.

    :param config: VoiceGatewayConfig instance.
    :return: Tuple of (is_valid: bool, error_message: Optional[str]).
             If authentication passes or is disabled, returns (True, None).
    """
    if not config.auth_enabled:
        return True, None

    expected_key = config.get_api_key()
    if not expected_key:
        # Auth enabled flag set but no key configured -> disable auth for local dev
        return True, None

    provided_key = None

    # 1. Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[0].lower() in ("bearer", "key", "token"):
            provided_key = parts[1].strip()
        else:
            provided_key = auth_header.strip()

    # 2. Check X-API-Key header
    if not provided_key:
        provided_key = request.headers.get("X-API-Key")

    # 3. Check query parameter ?api_key=
    if not provided_key:
        provided_key = request.args.get("api_key")

    if not provided_key:
        return False, "API key required in Authorization header, X-API-Key header, or ?api_key parameter"

    if provided_key != expected_key:
        return False, "Invalid API key"

    return True, None


def require_api_key(config: VoiceGatewayConfig) -> Callable:
    """
    Flask route decorator that enforces API key authentication.

    :param config: VoiceGatewayConfig instance.
    :return: Decorated route handler.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            is_valid, err_msg = validate_api_key(config)
            if not is_valid:
                return jsonify({
                    "error": "Unauthorized",
                    "message": err_msg or "Authentication failed"
                }), 401
            return f(*args, **kwargs)
        return decorated_function
    return decorator
