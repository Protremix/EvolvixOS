# Contributing to EvolvixOS

Thank you for your interest in contributing to EvolvixOS! This guide will help you get started.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Git
- Ubuntu 22.04+ (recommended for full functionality)
- Optional: Ollama for local LLM inference
- Optional: Go 1.21+ for the Tencent Cloud CLI binary

### Setup

```bash
git clone https://github.com/Protremix/EvolvixOS.git
cd EvolvixOS
pip3 install -r requirements.txt

# Start core services
python3 models/model_api.py &  # Model API on :5010
python3 auth/auth_api.py &      # Auth API on :5000
python3 dashboard/server.py &   # Dashboard on :8080
```

## 📋 Development Workflow

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Commit changes**: `git commit -m "Add: description of your change"`
4. **Push**: `git push origin feature/your-feature-name`
5. **Open a Pull Request**

### Commit Message Convention

Use clear, descriptive commit messages:

- `Add: new tool for X`
- `Fix: resolved issue with Y`
- `Update: improved Z performance`
- `Docs: updated README section`

## 🧪 Testing

Before submitting a PR:

```bash
# Test the health endpoint
curl http://localhost:5010/api/health

# Test agent streaming
curl -X POST http://localhost:5010/api/agent \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, what tools do you have?"}'
```

## 🔒 Security

- **Never commit secrets, API keys, or credentials**
- Use environment variables for all sensitive configuration
- Report security vulnerabilities privately to the maintainers
- Follow the SSRF guard patterns when making external HTTP requests

## 📁 Project Structure

```
EvolvixOS/
├── agent/          # Mr James AI agent code
├── auth/           # Authentication API (JWT, OTP, API keys)
├── dashboard/      # Frontend pages (landing, studio, models, APIs)
├── docs/           # GitHub Pages documentation site
├── knowledge/       # Subagent templates & MBTI profiles
├── learner/        # GitHub Discovery Engine
├── memory/         # TencentDB Agent Memory config
├── models/         # Model API, tool definitions, integrations
├── skills/         # Custom skill scripts
├── tccli/          # Go binary for Tencent Cloud CLI
└── web/            # Additional web interfaces
```

## 💡 Areas for Contribution

- **New Tools**: Add new tools to Mr James's toolkit
- **Model Support**: Add support for new local LLM models
- **UI/UX**: Improve dashboard pages and the docs site
- **Integrations**: Add new third-party service integrations
- **Documentation**: Improve docs, add examples, write tutorials
- **Testing**: Add test coverage for existing tools
- **Security**: Audit and improve security measures

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.
