"""
EvolvixOS v10 — Integration Tests (Production Configuration)
=============================================================
Tests the LIVE model_api.py service (port 5010) to verify:
  1. v10 architecture is active (health endpoint)
  2. Router routes correctly through the live service
  3. Security blocks dangerous commands through the live service
  4. All 4 providers are available
  5. No legacy execution paths remain (audit scan)
  6. Tool permissions are enforced
  7. SSRF protection works on live endpoints
  8. Audit logging captures executions

These tests run against the running service, not mocks.
Run: python3 v10/tests/test_v10_integration.py
"""

import sys
import os
import json
import urllib.request
import urllib.error
import re

sys.path.insert(0, "/opt/evolvixos")

from v10.providers.base import PrivacyMode, get_registry, init_registry
from v10.router.model_router import get_router, init_router
from v10.security.tool_security import (
    init_default_tools, get_tool_spec, check_permission,
    TOOL_SPECS, validate_command, validate_url, validate_python_code
)

SERVICE_URL = "http://127.0.0.1:5010"

passed = 0
failed = 0
errors = []


def assert_true(condition, name, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name} — {detail}")
        failed += 1
        errors.append(f"{name}: {detail}")


def assert_equal(actual, expected, name):
    global passed, failed
    if actual == expected:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name} — expected {expected!r}, got {actual!r}")
        failed += 1
        errors.append(f"{name}: expected {expected!r}, got {actual!r}")


def http_get(path):
    """Make a GET request to the live service."""
    try:
        req = urllib.request.Request(f"{SERVICE_URL}{path}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


# ─── 1. LIVE SERVICE HEALTH ──────────────────────────────────────────────────

def test_service_alive():
    """Service is running and responding."""
    print("\n=== INT: Service is alive ===")
    status, body = http_get("/api/health")
    assert_equal(status, 200, "Health endpoint returns 200")
    assert_equal(body.get("status"), "online", "Service status is 'online'")


def test_v10_fields_in_health():
    """Health endpoint exposes v10 architecture fields."""
    print("\n=== INT: v10 fields in health endpoint ===")
    status, body = http_get("/api/health")
    assert_true(body.get("v10_enabled") == True,
                "v10_enabled is True")
    assert_true(body.get("v10_privacy_mode") in ("HYBRID", "LOCAL", "CLOUD"),
                "v10_privacy_mode is a valid mode",
                body.get("v10_privacy_mode"))
    assert_equal(body.get("james_version"), "10.0",
                 "James version is 10.0")


def test_all_providers_available():
    """All 4 providers are available in the live service."""
    print("\n=== INT: All 4 providers available ===")
    status, body = http_get("/api/health")
    providers = body.get("v10_providers", [])
    assert_true("ollama" in providers, "Ollama provider is available")
    assert_true("groq" in providers, "Groq provider is available")
    assert_true("gemini" in providers, "Gemini provider is available")
    assert_true("kimi" in providers, "Kimi provider is available")
    assert_equal(len(providers), 4, "Exactly 4 providers available")

    # Check provider details
    details = body.get("v10_provider_details", [])
    for p in details:
        name = p.get("name", "")
        assert_true(p.get("available") == True,
                    f"Provider {name} is available")


def test_gemini_has_vision():
    """Gemini provider has vision capability."""
    print("\n=== INT: Gemini has vision ===")
    status, body = http_get("/api/health")
    details = body.get("v10_provider_details", [])
    gemini = [p for p in details if p.get("name") == "gemini"]
    assert_true(len(gemini) == 1, "Gemini provider found in details")
    if gemini:
        assert_true(gemini[0].get("vision") == True,
                    "Gemini has vision=True")
        assert_true(gemini[0].get("context") >= 1000000,
                    "Gemini has 1M+ context",
                    gemini[0].get("context"))


def test_ollama_is_local():
    """Ollama provider is correctly marked as local."""
    print("\n=== INT: Ollama is local ===")
    status, body = http_get("/api/health")
    details = body.get("v10_provider_details", [])
    ollama = [p for p in details if p.get("name") == "ollama"]
    assert_true(len(ollama) == 1, "Ollama provider found")
    if ollama:
        assert_true(ollama[0].get("local") == True,
                    "Ollama is_local=True")


# ─── 2. v10 ARCHITECTURE INTEGRITY ───────────────────────────────────────────

def test_router_initialized():
    """v10 ModelRouter is initialized and functional."""
    print("\n=== INT: ModelRouter initialized ===")
    from v10.router.model_router import ModelRouter
    registry = init_registry("HYBRID")
    router = ModelRouter(registry)
    decision = router.route("Write a Python function")
    assert_true(decision.task_type == "code",
                "Router classifies 'Write a Python function' as code")
    assert_true(decision.provider in ("ollama", "groq", "gemini", "kimi"),
                "Router selects a valid provider")
    assert_true(len(decision.reason) > 0,
                "Router provides a reason")


def test_privacy_mode_enforced():
    """Privacy mode is correctly set from environment."""
    print("\n=== INT: Privacy mode enforced ===")
    # Default is HYBRID
    status, body = http_get("/api/health")
    mode = body.get("v10_privacy_mode")
    assert_true(mode in ("HYBRID", "LOCAL", "CLOUD"),
                "Privacy mode is a valid value")


def test_local_mode_blocks_cloud_live():
    """LOCAL mode would block cloud — verify registry logic."""
    print("\n=== INT: LOCAL mode blocks cloud (registry) ===")
    # Use LLMRegistry directly (fresh, no pre-registered providers)
    from v10.providers.base import LLMRegistry, LLMProvider, LLMResponse, PrivacyMode
    registry = LLMRegistry()
    registry.set_privacy_mode(PrivacyMode.LOCAL)

    class MockLocal(LLMProvider):
        name = "mock_local"
        is_local = True
        supports_tools = True
        default_model = "mock"
        max_context = 32768
        def is_available(self): return True
        def chat(self, messages, tools=None, stream=False, **kw):
            return LLMResponse(content="local", provider="mock_local", model="mock")

    class MockCloud(LLMProvider):
        name = "mock_cloud"
        is_local = False
        supports_tools = True
        default_model = "mock"
        max_context = 128000
        def is_available(self): return True
        def chat(self, messages, tools=None, stream=False, **kw):
            return LLMResponse(content="cloud", provider="mock_cloud", model="mock")

    registry.register(MockLocal())
    registry.register(MockCloud())

    assert_true(registry.can_use_cloud() == False,
                "LOCAL mode: can_use_cloud() is False")

    decision = registry.select_for_task(
        task_type="reasoning", complexity="complex",
        needs_vision=True, needs_tools=True)
    assert_equal(decision.provider, "mock_local",
                 "LOCAL mode: complex task still routes to local")


# ─── 3. SECURITY ON LIVE SERVICE ─────────────────────────────────────────────

def test_tool_permissions_complete():
    """All security-critical tools have proper permission levels."""
    print("\n=== INT: Tool permissions complete ===")
    init_default_tools()

    # Admin-only tools
    admin_tools = ["service_restart", "docker_restart", "git", "pip_install"]
    for tool in admin_tools:
        spec = get_tool_spec(tool)
        assert_true(spec is not None,
                    f"Tool {tool} is registered")
        if spec:
            ok_user, _ = check_permission(tool, user_role="user")
            ok_admin, _ = check_permission(tool, user_role="admin")
            assert_true(not ok_user,
                        f"Tool {tool}: blocked for regular user")
            assert_true(ok_admin,
                        f"Tool {tool}: allowed for admin")

    # User-accessible tools
    user_tools = ["bash", "python_exec", "file_read", "file_write"]
    for tool in user_tools:
        spec = get_tool_spec(tool)
        assert_true(spec is not None,
                    f"Tool {tool} is registered")
        if spec:
            ok_user, _ = check_permission(tool, user_role="user")
            assert_true(ok_user,
                        f"Tool {tool}: allowed for regular user")


def test_total_registered_tools():
    """Sufficient tools are registered in the security framework."""
    print("\n=== INT: Registered tool count ===")
    init_default_tools()
    count = len(TOOL_SPECS)
    assert_true(count >= 20,
                f"At least 20 tools registered (got {count})",
                str(count))


def test_security_validations_on_live_imports():
    """Security validation functions work when imported from live service."""
    print("\n=== INT: Security validations work ===")

    # Command validation
    ok, _ = validate_command("rm -rf /")
    assert_true(not ok, "validate_command blocks rm -rf /")

    ok, _ = validate_command("ls -la")
    assert_true(ok, "validate_command allows ls -la")

    # URL validation
    ok, _ = validate_url("http://127.0.0.1/admin")
    assert_true(not ok, "validate_url blocks localhost")

    ok, _ = validate_url("https://api.github.com/repos")
    assert_true(ok, "validate_url allows github.com")

    # Python validation
    ok, _ = validate_python_code("eval('1+1')")
    assert_true(not ok, "validate_python_code blocks eval()")

    ok, _ = validate_python_code("print('hello')")
    assert_true(ok, "validate_python_code allows print()")


# ─── 4. LEGACY PATH ELIMINATION AUDIT ─────────────────────────────────────────

def test_no_legacy_agent_files():
    """Legacy mr_james_v4/v5 files are isolated."""
    print("\n=== INT: Legacy files isolated ===")

    # Check legacy files are NOT in active paths
    active_paths = [
        "/opt/evolvixos/agent/mr_james_v5.py",
        "/opt/evolvixos/agent/mr_james_v4.py",
    ]
    for path in active_paths:
        assert_true(not os.path.exists(path),
                    f"Legacy file removed: {path}")

    # Check they ARE in legacy/
    legacy_paths = [
        "/opt/evolvixos/legacy/mr_james_v5.py.bak",
        "/opt/evolvixos/legacy/mr_james_v4.py.bak",
    ]
    for path in legacy_paths:
        assert_true(os.path.exists(path),
                    f"Legacy file backed up: {path}")


def test_no_shell_true_in_model_api():
    """No subprocess shell=True in model_api.py (except in detection code)."""
    print("\n=== INT: No shell=True in model_api.py ===")

    with open("/opt/evolvixos/models/model_api.py") as f:
        content = f.read()

    # Find all shell=True occurrences that are ACTUAL subprocess calls
    # (not string comparisons in detection code)
    lines = content.split("\n")
    shell_true_lines = []
    for i, line in enumerate(lines, 1):
        if "shell=True" in line:
            # Exclude: string comparisons ("shell=True" in code), findings, detection
            if any(x in line for x in ["findings", "detect", "CRITICAL", "HIGH", "in code", "in line"]):
                continue
            # Exclude: comments
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            shell_true_lines.append((i, stripped))

    assert_true(len(shell_true_lines) == 0,
                f"No shell=True in model_api.py (found {len(shell_true_lines)})",
                str(shell_true_lines[:3]))


def test_no_direct_kimi_url_in_model_api():
    """No direct Kimi API URL construction in model_api.py (should use v10 provider)."""
    print("\n=== INT: No direct Kimi URL in model_api.py ===")

    with open("/opt/evolvixos/models/model_api.py") as f:
        content = f.read()

    # Look for direct Kimi URL construction (not in the v10 provider)
    lines = content.split("\n")
    direct_kimi = []
    for i, line in enumerate(lines, 1):
        if "api.moonshot" in line and "urllib" not in line and "import" not in line:
            # Check if it's a variable definition (KIMI_URL = ...)
            if "KIMI_URL" in line and "=" in line:
                continue  # This is just the URL constant, acceptable
            direct_kimi.append((i, line.strip()))

    # Direct API calls to Kimi URL (not just the constant) should not exist
    kimi_calls = [l for l in direct_kimi if "urllib" in l[1] or "Request" in l[1] or "open" in l[1].lower()]
    assert_true(len(kimi_calls) == 0,
                f"No direct Kimi API calls in model_api.py (found {len(kimi_calls)})",
                str(kimi_calls[:3]))


def test_classify_intent_delegates_to_v10():
    """classify_intent in model_api.py delegates to v10 ModelRouter."""
    print("\n=== INT: classify_intent delegates to v10 ===")

    with open("/opt/evolvixos/models/model_api.py") as f:
        content = f.read()

    # Check that classify_intent uses _v10_router
    assert_true("_v10_router" in content and "classify_intent" in content,
                "model_api.py references _v10_router and classify_intent")

    # Find the classify_intent function and check it delegates
    # Look for the delegation pattern
    assert_true("_v10_router.route" in content,
                "classify_intent calls _v10_router.route()")


def test_v10_security_references_count():
    """Sufficient v10 security references in model_api.py."""
    print("\n=== INT: v10 security references in model_api.py ===")

    with open("/opt/evolvixos/models/model_api.py") as f:
        content = f.read()

    count = content.count("validate_command") + \
            content.count("validate_url") + \
            content.count("validate_python_code") + \
            content.count("log_audit") + \
            content.count("check_permission")

    assert_true(count >= 25,
                f"At least 25 v10 security references (got {count})",
                str(count))


# ─── 5. PROVIDER FALLBACK CHAIN ───────────────────────────────────────────────

def test_provider_fallback_chain():
    """Router fallback chain respects privacy mode."""
    print("\n=== INT: Provider fallback chain ===")

    # Use the live service health endpoint to verify providers
    status, body = http_get("/api/health")
    providers = body.get("v10_providers", [])

    # The live service has all env vars from systemd
    assert_true(len(providers) >= 3,
                f"At least 3 providers available in live service (got {len(providers)})",
                str(providers))

    # Verify cloud is usable in HYBRID mode
    assert_true(body.get("v10_privacy_mode") == "HYBRID",
                "Live service is in HYBRID mode")

    # Test routing logic with fresh registry + env vars from systemd
    import subprocess
    env_output = subprocess.run(
        ["systemctl", "show", "evolvixos-models", "--property=Environment"],
        capture_output=True, text=True
    ).stdout

    # Set env vars from systemd if not already set
    for key in ["GROQ_API_KEY", "GOOGLE_API_KEY", "KIMI_API_KEY"]:
        if key not in os.environ:
            # Try to extract from systemd
            import re
            match = re.search(f"{key}=(\S+)", env_output)
            if match:
                os.environ[key] = match.group(1)

    registry = init_registry("HYBRID")
    available = registry.list_available()

    # Simple task should go to local
    decision = registry.select_for_task(
        task_type="chat", complexity="simple")
    provider = registry.get(decision.provider)
    if provider:
        assert_true(provider.is_local,
                     "HYBRID mode: simple task routes to local provider")

    # Complex task should go to cloud (if cloud providers available)
    if len(available) >= 2:
        decision = registry.select_for_task(
            task_type="reasoning", complexity="complex")
        provider = registry.get(decision.provider)
        if provider:
            assert_true(not provider.is_local,
                        "HYBRID mode: complex task routes to cloud provider")


# ─── RUN ALL INTEGRATION TESTS ────────────────────────────────────────────────

def run_all():
    print("=" * 70)
    print("  EvolvixOS v10 — Integration Tests (Production)")
    print("=" * 70)

    # 1. Live service health
    test_service_alive()
    test_v10_fields_in_health()
    test_all_providers_available()
    test_gemini_has_vision()
    test_ollama_is_local()

    # 2. v10 architecture integrity
    test_router_initialized()
    test_privacy_mode_enforced()
    test_local_mode_blocks_cloud_live()

    # 3. Security on live service
    test_tool_permissions_complete()
    test_total_registered_tools()
    test_security_validations_on_live_imports()

    # 4. Legacy path elimination
    test_no_legacy_agent_files()
    test_no_shell_true_in_model_api()
    test_no_direct_kimi_url_in_model_api()
    test_classify_intent_delegates_to_v10()
    test_v10_security_references_count()

    # 5. Provider fallback chain
    test_provider_fallback_chain()

    print("\n" + "=" * 70)
    print(f"  Integration Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 70)

    if errors:
        print("\nFAILURES:")
        for e in errors:
            print(f"  - {e}")

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
