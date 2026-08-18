#!/bin/bash
cd /opt/evolvixos

echo "=== AUDIT: Direct Ollama calls bypassing v10 ModelRouter ==="
grep -n 'ollama\|localhost:11434\|requests.post.*ollama\|http.*11434' model_api.py | grep -v '#\|comment\|doc\|v10\|router\|_v10' | head -20
echo ""

echo "=== AUDIT: Direct Kimi/Groq/Gemini API calls bypassing v10 ==="
grep -n 'api.moonshot\|api.groq\|generativelanguage.googleapis\|kimi\|groq\|gemini' model_api.py | grep -v '#\|comment\|doc\|v10\|router\|_v10\|import\|config\|env\|var\|="\|='" | head -20
echo ""

echo "=== AUDIT: shell=True or subprocess without v10 security ==="
grep -n 'shell=True\|os.system\|subprocess.call\|os.popen' model_api.py | grep -v '#\|comment\|v10\|security\|validate' | head -20
echo ""

echo "=== AUDIT: Direct tool execution without permission checks ==="
grep -n 'def.*tool\|def.*handle\|def.*exec' model_api.py | head -30
echo ""

echo "=== AUDIT: Legacy imports ==="
grep -n 'import.*mr_james\|from.*mr_james\|from agent import' model_api.py | head -10
echo ""

echo "=== AUDIT: Direct fetch/requests without SSRF check ==="
grep -n 'requests.get\|requests.post\|urllib\|httpx' model_api.py | grep -v '#\|v10\|security\|validate_url\|SSRF' | head -20
echo ""

echo "=== AUDIT: Any remaining _handle_stream_chat direct calls ==="
grep -n '_handle_stream_chat\|stream_chat\|generate_text' model_api.py | head -20
