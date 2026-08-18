# Tool Reference

Complete documentation for all 44 Mr James tools.

## File Operations

### file_read
Read file contents from the server.
```json
{"name": "file_read", "args": {"file_path": "/path/to/file"}}
```

### file_write
Write content to a file (creates or overwrites).
```json
{"name": "file_write", "args": {"file_path": "/path/to/file", "content": "..."}}
```

### file_edit
Edit an existing file (find and replace).
```json
{"name": "file_edit", "args": {"file_path": "/path", "old_text": "...", "new_text": "..."}}
```

### file_list
List directory contents.
```json
{"name": "file_list", "args": {"dir_path": "/path/to/dir"}}
```

### file_delete
Delete a file.
```json
{"name": "file_delete", "args": {"file_path": "/path/to/file"}}
```

### code_analyze
Analyze code with AI (uses Gemini Vision for images, Groq for code).
```json
{"name": "code_analyze", "args": {"path": "file.py", "language": "python"}}
```

## Code Execution

### python_exec
Execute Python code on the server.
```json
{"name": "python_exec", "args": {"code": "print('hello')"}}
```

### bash_exec
Execute shell commands (shlex.split, shell=False for security).
```json
{"name": "bash_exec", "args": {"command": "ls -la /opt"}}
```

### sandbox_exec
Execute code in CubeSandbox (Docker-isolated).
```json
{"name": "sandbox_exec", "args": {"code": "import numpy; print(numpy.__version__)", "language": "python"}}
```

## AI / LLM

### call_free_llm
Delegate to 442+ free LLM APIs across 31 providers.
```json
{"name": "call_free_llm", "args": {"prompt": "Explain quantum computing", "model": "auto"}}
```

### gemini_vision
Analyze images, OCR, charts, UI screenshots.
```json
{"name": "gemini_vision", "args": {"image_path": "/path/to/image.png", "prompt": "What's in this image?"}}
```

### gemini_tts
Text-to-speech via Gemini.
```json
{"name": "gemini_tts", "args": {"text": "Hello world", "voice": "en-US"}}
```

### file_upload
Upload file with Gemini Vision analysis (50MB max).
```json
{"name": "file_upload", "args": {"file_path": "document.pdf"}}
```

## Smart API

### api_auto_route
Semantic API discovery across 35,277 resources.
```json
{"name": "api_auto_route", "args": {"query": "weather API", "category": "weather"}}
```

### smart_api_call
Execute an HTTP API call.
```json
{"name": "smart_api_call", "args": {"url": "https://api.example.com/data", "method": "GET"}}
```

### http_request
Generic HTTP request.
```json
{"name": "http_request", "args": {"url": "https://...", "method": "POST", "body": {}}}
```

## Tencent Cloud

### tencent_cloud
Unified Tencent Cloud API (12 Python + 7 Go services).
```json
{"name": "tencent_cloud", "args": {"service": "cvm", "action": "DescribeInstances", "params": {}}}
```

## TIMSDK Chat

### tim_send_message
Send a direct message via TIMSDK.
```json
{"name": "tim_send_message", "args": {"to_user": "user123", "message": "Hello"}}
```

### tim_create_group
Create a chat group.
```json
{"name": "tim_create_group", "args": {"group_name": "Team Chat", "type": "Public"}}
```

### tim_send_group_message
Send a message to a group.
```json
{"name": "tim_send_group_message", "args": {"group_id": "group123", "message": "Hi team"}}
```

### tim_import_user
Import a user into TIM.
```json
{"name": "tim_import_user", "args": {"user_id": "user123", "nickname": "Alice"}}
```

## Team Memory

### team_memory_search
Search TencentDB team memory with full-text search.
```json
{"name": "team_memory_search", "args": {"query": "deployment notes"}}
```

### team_memory_save
Save a memory to TencentDB.
```json
{"name": "team_memory_save", "args": {"content": "Deployed v9.2 at 3pm", "metadata": {"type": "log"}}}
```

## Agent Library

### search_subagents
Search 217 subagent templates across 16 categories.
```json
{"name": "search_subagents", "args": {"query": "security audit", "category": "security"}}
```

### set_persona
Switch MBTI personality profile.
```json
{"name": "set_persona", "args": {"mbti_type": "INTJ"}}
```

## System

### get_system_info
Get server status, CPU, RAM, disk usage.
```json
{"name": "get_system_info", "args": {}}
```

### manage_services
Start/stop/restart systemd services.
```json
{"name": "manage_services", "args": {"action": "restart", "service": "evolvix-model-api"}}
```

### get_service_logs
View service logs.
```json
{"name": "get_service_logs", "args": {"service": "evolvix-model-api", "lines": 50}}
```
