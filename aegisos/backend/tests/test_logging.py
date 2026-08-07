"""Tests for standardized logging configuration."""

import pytest
import logging
import structlog
from app.core.logging import get_logger, setup_logging


class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger_returns_logger(self):
        logger = get_logger("test_module_1")
        assert logger is not None

    def test_get_logger_supports_kwargs(self):
        """structlog should support arbitrary kwargs in log calls."""
        logger = get_logger("test_kwargs")
        # This should not raise
        logger.info("test_event", request_id="req-123", user_id="user-456")

    def test_get_logger_different_names(self):
        logger1 = get_logger("test_module_3")
        logger2 = get_logger("test_module_4")
        assert logger1 is not logger2

    def test_get_logger_accepts_default_name(self):
        logger = get_logger()
        assert logger is not None


class TestSetupLogging:
    """Test the setup_logging function."""

    def test_setup_logging_json_mode(self):
        # setup_logging calls logging.basicConfig which sets root level
        setup_logging(json_mode=True, level="DEBUG")
        # Verify structlog is configured
        config = structlog.get_config()
        assert "processors" in config

    def test_setup_logging_text_mode(self):
        setup_logging(json_mode=False, level="WARNING")
        config = structlog.get_config()
        assert "processors" in config

    def test_setup_logging_default(self):
        setup_logging()
        config = structlog.get_config()
        assert "processors" in config


class TestLoggingIntegration:
    """Test logging works with the rest of the system."""

    def test_error_handler_logger_works(self):
        """Verify the error handler pattern works with structlog."""
        logger = get_logger("app.middleware.error_handler")
        logger.warning(
            "http_exception",
            request_id="req-test-123",
            status_code=401,
            detail="Unauthorized",
            path="/api/v1/test",
        )

    def test_service_logger_works(self):
        """Verify service-level logging with kwargs."""
        logger = get_logger("app.services.dependency_graph")
        logger.info(
            "graph_built",
            project_path="/test/path",
            total_files=42,
            total_deps=100,
        )

    def test_ai_agent_logger_works(self):
        """Verify AI agent logging with kwargs."""
        logger = get_logger("app.ai.agents.cto_agent")
        logger.info(
            "task_completed",
            task_type="code_review",
            duration_ms=1500,
            tokens_used=500,
        )

    def test_log_levels(self):
        """Test all log levels work."""
        logger = get_logger("test_levels")
        logger.debug("debug_msg")
        logger.info("info_msg")
        logger.warning("warning_msg")
        logger.error("error_msg")
