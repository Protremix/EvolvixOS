# EvolvixOS VS Code Extension

Chat with 435+ AI models directly from VS Code.

## Features

- **Chat with AI** — Ask any question, get a response in a webview panel
- **Code Review** — Select code, ask AI to review it, output in a dedicated channel
- **Auto-routing** — Uses `auto` model by default (picks the best model per task)
- **Configurable** — Set custom platform URL and default model

## Usage

1. Install the extension
2. Run `EvolvixOS: Set API Key` and enter your key
3. Run `EvolvixOS: Chat with AI` to ask a question
4. Select code and run `EvolvixOS: Stream Response` for code review

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `evolvixos.baseUrl` | `https://evolvixos.com` | Platform URL |
| `evolvixos.defaultModel` | `auto` | Default model |

## Requirements

- An EvolvixOS account (sign up free at [evolvixos.com](https://evolvixos.com))
- An API key (get it from the dashboard)

License: MIT
