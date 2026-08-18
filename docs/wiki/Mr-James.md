# Mr James v9.2

Mr James is the autonomous AI agent at the heart of EvolvixOS. It uses triple-brain routing to select the best AI engine for each task, and has access to 44 tools for file operations, code execution, API calls, cloud management, messaging, and memory.

## Triple-Brain Routing

Mr James analyzes the user's intent and routes to the optimal engine:

```
User Prompt → Intent Analysis → Engine Selection
                                    │
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
                 Groq           Gemini          Kimi
              (tool-use)    (vision/large)   (reasoning)
                    │               │               │
                    └───────┬───────┘               │
                            ↓                       │
                         Ollama ←───────────────────┘
                        (fallback)
```

### Engine Selection Logic

| Intent | Engine | Reason |
|--------|--------|--------|
| Tool use / code execution | Groq | Best tool-call precision at 467 tok/s |
| Vision / image / large context | Gemini | 1M context, multimodal |
| Complex reasoning / analysis | Kimi | moonshot-v1-32k reasoning |
| Simple chat / offline | Ollama | Local, zero-cost |
| File upload / OCR | Gemini | Vision capability |

## Tool Execution Loop

1. User sends prompt
2. Mr James analyzes intent
3. Routes to selected engine with tool definitions
4. Engine responds with text and/or tool calls
5. Tools execute on the server
6. Results fed back to engine
7. Engine generates final response
8. Response streamed to user

## Conversation Management

- Per-user conversation history (JSON files in `/opt/evolvixos/conversations/`)
- Context window management (summarization for long conversations)
- Multi-session support per user
