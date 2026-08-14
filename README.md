<div align="center">

# 🧬 EvolvixOS

### The Open-Source AI Engineering Platform

**100% Local · Zero Tokens · Zero Cloud · Zero Subscriptions · Free Forever**

*Just type what you need. EvolvixOS builds it, manages it, and handles everything — including your real life.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests: 186](https://img.shields.io/badge/Tests-186%2F186-brightgreen.svg)](#testing)
[![Benchmark: 490](https://img.shields.io/badge/Benchmark-490%2F490-brightgreen.svg)](#testing)
[![Skills: 439](https://img.shields.io/badge/Skills-439+-orange.svg)](#skills)
[![Templates: 11K](https://img.shields.io/badge/Templates-11K-orange.svg)](#templates)
[![Cost: $0](https://img.shields.io/badge/Cost-$0.00-success.svg)](#philosophy)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](#deployment)

</div>

---

## Table of Contents

- [Overview](#overview)
- [What Makes It Different](#what-makes-it-different)
- [The Genie — Zero-Code Builder](#the-genie--zero-code-builder)
- [Real Life AI Assistant](#real-life-ai-assistant)
- [The Ecosystem](#the-ecosystem)
- [Skills (439+)](#skills)
- [REST API (800+ Endpoints)](#rest-api)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [Testing](#testing)
- [Philosophy](#philosophy)

---

## Overview

EvolvixOS is a fully autonomous, self-improving AI engineering platform that runs entirely on your hardware. No cloud. No API keys. No tokens. No subscriptions. It discovers, installs, and learns from open-source AI tools across GitHub — getting continuously smarter without spending a single cent.

**What can it do?**

- 🧞 **Build anything** — Just type what you need in plain English. No coding required.
- 🤖 **Manage your real life** — Tasks, calendar, budget, goals, shopping, reminders, daily briefings.
- 📞 **Answer phone calls** — Add a VoIP API and EvolvixOS answers calls with AI voice.
- 🔌 **Connect to any API** — Register any external API and EvolvixOS manages it.
- 🏠 **Control any device** — Smart home, computers, phones, IoT. Auto-discovers on your network.
- 🧞 **Spawn sub-agents** — Parallel AI workers handle multiple tasks simultaneously.
- 🧬 **Learn from GitHub** — Discovers and installs new AI skills automatically.
- 🎬 **Create movies** — Full cinematic pipeline with local AI video generation.
- 🗣️ **Real voice** — Local Whisper (STT) + Kokoro (TTS). No cloud voice services.
- 🚀 **Deploy anywhere** — One command to your own server with Docker.

---

## What Makes It Different

| Feature | ChatGPT / Claude / Kimi | EvolvixOS |
|---------|------------------------|-----------|
| **Cost** | $20-200/month, per-token pricing | **$0.00 forever** |
| **Privacy** | Data sent to cloud servers | **Stays on your machine** |
| **API for your projects** | Rate-limited, paid per request | **Unlimited, free, local** |
| **Learns your codebase** | Limited context window | **Deep project understanding** |
| **Real voice** | Cloud TTS/STT services | **Local Whisper + Kokoro** |
| **Answers phone calls** | No | **Yes — with any VoIP API** |
| **Smart home control** | No | **Yes — any device, any platform** |
| **Learns from GitHub** | No | **Yes — auto-discovers & installs AI skills** |
| **Sub-agents** | Limited | **Up to 10 parallel workers** |
| **Gets smarter over time** | Model updates only | **Every GitHub skill makes it smarter** |
| **Self-hosted** | No | **Yes — your server, your rules** |
| **Zero-code builder** | No | **Yes — the Genie builds anything from plain English** |
| **Life management** | No | **Tasks, calendar, budget, goals, shopping, reminders** |
| **Video generation** | Cloud, expensive | **Wan 2.1, local, free** |
| **Marketing / ads** | Billion-dollar budgets | **None. Build free. Teach him. Enjoy.** |

---

## The Genie — Zero-Code Builder

Don't know how to code? No problem. The Genie builds complete projects from plain English descriptions.

### How it works:

```
User: "I need a website for my bakery"
                    ↓
🧞 Genie understands: type=website, features=[menu, gallery, contact, hours]
                    ↓
🔧 Genie builds: HTML, CSS, JavaScript, responsive design, SEO
                    ↓
🔍 Auto-audit: scans for XSS, SQL injection, secrets, vulnerabilities
                    ↓
🛡️ Auto-fix: parameterizes SQL, escapes XSS, adds validation, removes secrets
                    ↓
✅ Security protocol: 10-point enforcement (input validation, output encoding,
   SQL parameterization, secret management, path traversal protection,
   command injection protection, security headers, rate limiting, CSRF, XSS)
                    ↓
📦 Ready-to-use project delivered with instructions
```

### 10 project types:

| Type | What you get |
|------|-------------|
| 🌐 Website | Full responsive site from 11K template library |
| 🖥️ Web App | Flask + HTML application |
| 📱 Mobile App | PWA — works on Android, iOS, Windows |
| 🔗 REST API | With auth, rate limiting, security headers |
| 💬 Chatbot | Web interface + NLP |
| 📊 Data Analysis | Python script with statistics |
| ⚙️ Automation | Scheduled task runner |
| 📄 Document | HTML report → PDF |
| 📈 Dashboard | Live metrics + charts |
| 🎮 Game | HTML5 interactive game |

### API:

```bash
# Build from natural language
curl -X POST http://localhost:5001/api/v1/genie \
  -H "Content-Type: application/json" \
  -d '{"request": "I need a REST API for a todo app with auth"}'

# Understand intent without building
curl -X POST http://localhost:5001/api/v1/genie/understand \
  -H "Content-Type: application/json" \
  -d '{"request": "Build me a mobile app for tracking workouts"}'
```

---

## Real Life AI Assistant

EvolvixOS doesn't just build apps — it manages your entire life.

### 🧞 Sub-Agents

Spawn background AI workers to handle multiple tasks in parallel:

```bash
# Spawn a single agent
curl -X POST http://localhost:5001/api/v1/agents/spawn \
  -d '{"task_name": "analyze_code", "skill_name": "code_analyzer", "args": {"path": "./src"}}'

# Run multiple skills in parallel
curl -X POST http://localhost:5001/api/v1/agents/run \
  -d '{"tasks": [{"skill": "code_analyzer", "args": {}}, {"skill": "security_scanner", "args": {}}]}'

# Check status
curl http://localhost:5001/api/v1/agents/{agent_id}
```

### 📞 VoIP Call Answering

Add a VoIP API (Twilio, Vonage, SIP) and EvolvixOS becomes a real human on the phone:

```bash
# Set up Twilio
curl -X POST http://localhost:5001/api/v1/voip/setup \
  -d '{"provider": "twilio", "account_sid": "...", "auth_token": "...", "from_number": "+1..."}'

# AI answers incoming calls with voice
curl -X POST http://localhost:5001/api/v1/voip/answer \
  -d '{"call_id": "CA...", "message": "Hello! How can I help you today?"}'

# Make outbound calls
curl -X POST http://localhost:5001/api/v1/voip/call \
  -d '{"to_number": "+1...", "message": "Hi, this is a reminder for your appointment"}'

# Send SMS
curl -X POST http://localhost:5001/api/v1/voip/sms \
  -d '{"to_number": "+1...", "body": "Your order is ready!"}'
```

### 🔌 Universal API Manager

Connect EvolvixOS to any external API:

```bash
# Register an API
curl -X POST http://localhost:5001/api/v1/apis/register \
  -d '{"name": "my_service", "base_url": "https://api.example.com", "auth_type": "bearer", "token": "..."}'

# Call it
curl -X POST http://localhost:5001/api/v1/apis/my_service/call \
  -d '{"method": "GET", "path": "/users/123"}'

# Chain multiple API calls
curl -X POST http://localhost:5001/api/v1/apis/chain \
  -d '{"calls": [{"name": "my_service", "method": "GET", "path": "/users"}, {"name": "my_service", "method": "POST", "path": "/summary"}]}'
```

### 🏠 Device Connector

Control any device or app:

```bash
# Register a smart light
curl -X POST http://localhost:5001/api/v1/devices/register \
  -d '{"name": "Living Room", "type": "light", "base_url": "http://192.168.1.50", "endpoints": {"on": "/on", "off": "/off"}}'

# Control it
curl -X POST http://localhost:5001/api/v1/devices/{id}/control \
  -d '{"command": "on", "value": 80}'

# Discover devices on your network
curl http://localhost:5001/api/v1/devices/discover
```

**Supported platforms:** Home Assistant, Philips Hue, Nest, Ring, Tesla, SmartThings, MQTT, and any REST device.

### 📋 Life Manager

Manage everything in your real life:

```bash
# Add a task
curl -X POST http://localhost:5001/api/v1/life/tasks \
  -d '{"title": "Finish quarterly report", "priority": "high", "due": "2026-08-20"}'

# Add a calendar event
curl -X POST http://localhost:5001/api/v1/life/events \
  -d '{"title": "Team meeting", "date": "2026-08-15T10:00:00", "duration": 60}'

# Track expenses
curl -X POST http://localhost:5001/api/v1/life/expenses \
  -d '{"amount": 45.99, "category": "groceries", "description": "Weekly shopping"}'

# Set a goal
curl -X POST http://localhost:5001/api/v1/life/goals \
  -d '{"title": "Learn Python", "milestones": ["Basics", "OOP", "Web frameworks"], "deadline": "2026-12-31"}'

# Get morning briefing
curl http://localhost:5001/api/v1/life/summary

# Get AI suggestions for what to do next
curl http://localhost:5001/api/v1/life/suggest
```

---

## The Ecosystem

EvolvixOS is part of a three-pillar ecosystem — all free, all open-source, all local.

```
┌─────────────────────────────────────────────────────────────┐
│                    THE EVOLVIXOS ECOSYSTEM                   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  🧬 EvolvixOS │  │ ⛓️ VerdisChain│  │  🌐 Anerium  │        │
│  │              │  │              │  │              │        │
│  │  AI Engine   │  │  Blockchain  │  │  Network     │        │
│  │  439+ skills │  │  Verifiable  │  │  P2P sharing │        │
│  │  Zero tokens │  │  Zero gas    │  │  Zero cost   │        │
│  │  Self-       │  │  Audit trail │  │  Federated    │        │
│  │  improving   │  │  Provenance  │  │  learning    │        │
│  │              │  │  Smart       │  │  Encrypted    │        │
│  │              │  │  contracts   │  │  Mesh network │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                              │
│  No corporation. No subscriptions. No ads. No marketing.    │
│  Build free. Teach him. Enjoy.                               │
└─────────────────────────────────────────────────────────────┘
```

### 🧬 EvolvixOS — The AI Engine
- 439+ skills (all local, all free)
- REST API with 800+ endpoints
- Voice assistant (Whisper + Kokoro)
- Self-improving via GitHub Discovery Engine
- One-command deployment to any server
- Zero-code builder (Genie)
- Real life management

### ⛓️ VerdisChain — The Blockchain Layer
- Immutable audit trail for AI decisions
- Zero-cost transactions (no gas fees)
- Provenance tracking for model outputs
- Decentralized skill verification
- Smart contracts for AI pipelines
- 100% local node operation

### 🌐 Anerium — The Network Layer
- Peer-to-peer skill sharing (free)
- Federated learning (local, private)
- Zero-cost mesh networking
- Encrypted by default
- No central server, no subscriptions

---

## Skills

EvolvixOS includes **439+ skills** — all run locally, all free. Here are the categories:

### Core AI Skills
| Skill | Description |
|-------|-------------|
| `agent/core` | Think → Plan → Act → Observe → Reflect loop |
| `github_discovery` | Searches GitHub for open-source AI tools, clones & learns |
| `self_improver` | Analyzes own performance and improves |
| `genie` | Zero-code natural language project builder |
| `sub_agents` | Spawn parallel AI worker agents |
| `intent_classifier` | Classifies user intent from natural language |
| `response_generator` | Generates contextual responses |
| `embeddings_engine` | Local text embeddings |
| `vector_store` | Local vector storage for semantic search |
| `nlp_processor` | Text processing and analysis |

### AI Engineering Platform
| Skill | Description |
|-------|-------------|
| `model_registry` | Register and manage ML models |
| `experiment_tracker` | Track ML experiments and results |
| `pipeline_builder` | Build ML pipelines |
| `pipeline_engine` | Execute ML pipelines |
| `evaluation` | Evaluate model performance |
| `ml_toolkit` | Complete ML toolkit |
| `kmeans_clustering` | K-Means clustering |
| `knearest_neighbors_classifier` | KNN classifier |
| `naive_bayes_classifier` | Naive Bayes |
| `decision_tree_simple` | Decision tree |
| `linear_regression_simple` | Linear regression |
| `logistic_sigmoid_calculator` | Logistic sigmoid |
| `train_test_split` | Train/test split |
| `feature_scaler` | Feature scaling |
| `label_encoder` | Label encoding |
| `one_hot_encoder` | One-hot encoding |
| `tfidf` | TF-IDF vectorization |
| `confusion_matrix` | Confusion matrix |
| `precision_recall` | Precision & recall |
| `f1_score` | F1 score |
| `roc_auc_calculator` | ROC AUC |
| `outlier_detector` | Outlier detection |

### Real Life Management
| Skill | Description |
|-------|-------------|
| `life_manager` | Tasks, calendar, contacts, budget, goals, shopping, reminders |
| `voip_calls` | Answer calls, make calls, send SMS via Twilio/Vonage/SIP |
| `device_connector` | Connect to any device or app |
| `api_manager` | Register and manage any external API |
| `scheduler` | Schedule recurring tasks |
| `scheduler_pro` | Advanced scheduling with cron |
| `email_sender` | Send emails |
| `email_validator` | Validate email addresses |
| `phone_validator` | Validate phone numbers |
| `postal_code_validator` | Validate postal codes |

### Development & DevOps
| Skill | Description |
|-------|-------------|
| `coding` | Code generation with Qwen2.5-Coder |
| `code_analyzer` | Analyze code quality |
| `code_linter` | Lint code |
| `code_runner` | Execute code safely |
| `dockerfile_linter` | Lint Dockerfiles |
| `kubernetes_yaml_validator` | Validate K8s manifests |
| `nginx_config_formatter` | Format Nginx configs |
| `bash_script_validator` | Validate bash scripts |
| `git_diff_parser` | Parse git diffs |
| `git_log_parser` | Parse git logs |
| `changelog_generator` | Generate changelogs |
| `deploy` | SSH deployment to any server |
| `hetzner_server` | Hetzner cloud server management |
| `systemd_service_generator` | Generate systemd services |
| `port_scanner` | Scan ports |
| `port_binding_checker` | Check port bindings |
| `ssl_checker` | Check SSL certificates |
| `ssl_cert_expiration_notifier` | SSL expiry alerts |
| `cors_checker` | Check CORS configuration |
| `http_headers_analyzer` | Analyze HTTP headers |
| `rest_api_tester` | Test REST APIs |
| `webhook_signature_verifier` | Verify webhook signatures |

### Security
| Skill | Description |
|-------|-------------|
| `auto_auditor` | Automatic security auditing |
| `auto_fixer` | Automatic code fixes |
| `security_scanner` | Scan for vulnerabilities |
| `security_scanner_pro` | Advanced security scanning |
| `security_header_checker` | Check security headers |
| `credential_validator` | Validate credentials |
| `password_strength` | Check password strength |
| `password_pwned_checker` | Check if password is breached |
| `bcrypt_hash_checker` | Verify bcrypt hashes |
| `hmac_generator` | Generate HMAC signatures |
| `rsa_key_generator` | Generate RSA keys |
| `fernet_encryption` | Fernet encryption |
| `shamir_secret_sharing` | Shamir's secret sharing |
| `otp_generator` | Generate OTPs |
| `totp_generator` | Generate TOTPs |
| `csrf_token_generator` | Generate CSRF tokens |
| `secure_random_bytes` | Generate secure random bytes |
| `salt_generator` | Generate salts |
| `entropy_checker` | Check entropy |
| `constant_time_compare` | Constant-time comparison |
| `environment_variable_sanitizer` | Sanitize env vars |
| `webhook_signature_verifier` | Verify webhook signatures |

### Media & Creative
| Skill | Description |
|-------|-------------|
| `video` | Video generation (Wan 2.1) |
| `movie_maker` | Full cinematic movie creation pipeline |
| `image` | Image generation (FLUX.1 schnell) |
| `image_editor` | Image editing |
| `image_processor` | Image processing |
| `audio` | Audio generation (MusicGen) |
| `audio_editor` | Audio editing |
| `audio_processor` | Audio processing |
| `voice` | Voice interaction (Whisper + Kokoro) |
| `voice_assistant` | Voice assistant |
| `ocr` | Optical character recognition |
| `ocr_scanner` | OCR scanning |
| `svg_generator` | Generate SVG graphics |
| `canvas_draw_commands` | Canvas drawing commands |
| `color_palette_generator` | Generate color palettes |
| `gradient_generator` | Generate gradients |
| `ascii_art` | ASCII art generation |
| `ascii_art_generator` | ASCII art generator |

### Data & Analysis
| Skill | Description |
|-------|-------------|
| `data_analyst` | Data analysis |
| `data_analyzer` | Data analysis tools |
| `data_compressor` | Compress data |
| `data_decompressor` | Decompress data |
| `data_normalizer` | Normalize data |
| `database_manager` | Database management |
| `csv_deduplicator` | Deduplicate CSVs |
| `csv_merger` | Merge CSVs |
| `csv_splitter` | Split CSVs |
| `csv_to_json` | CSV to JSON |
| `csv_transposer` | Transpose CSVs |
| `json_formatter` | Format JSON |
| `json_validator` | Validate JSON |
| `json_schema_validator` | Validate JSON Schema |
| `json_path_evaluator` | JSONPath evaluator |
| `json_to_csv` | JSON to CSV |
| `xml_parser` | Parse XML |
| `xml_to_json` | XML to JSON |
| `yaml_parser` | Parse YAML |
| `toml_parser` | Parse TOML |
| `ini_parser` | Parse INI files |
| `env_file_parser` | Parse .env files |
| `statistics_calc` | Statistics calculator |
| `statistics_calculator` | Advanced statistics |

### Web & Networking
| Skill | Description |
|-------|-------------|
| `browser_automation` | Browser automation |
| `web_crawler` | Web crawling |
| `web_scraper` | Web scraping |
| `web_scraper_light` | Lightweight web scraping |
| `feed_parser_rss` | RSS feed parser |
| `sitemap_parser` | Sitemap parser |
| `robots_txt_parser` | Robots.txt parser |
| `dns_lookup` | DNS lookup |
| `whois_lookup` | WHOIS lookup |
| `ip_geolocation` | IP geolocation |
| `ip_subnet_calculator` | Subnet calculator |
| `ip_range_expander` | IP range expander |
| `http_client` | HTTP client |
| `socket_client` | Socket client |
| `ping_tool` | Ping tool |
| `traceroute_helper` | Traceroute |
| `uptime_calculator` | Uptime calculator |
| `cdn_detector` | CDN detector |
| `url_parser` | URL parser |
| `url_encoder_decoder` | URL encoder/decoder |
| `query_string_builder` | Query string builder |
| `user_agent_parser` | User agent parser |

### Finance & Business
| Skill | Description |
|-------|-------------|
| `mortgage_calculator` | Mortgage calculator |
| `loan_calculator` | Loan calculator |
| `compound_interest` | Compound interest |
| `roi_calculator` | ROI calculator |
| `npv_calculator` | NPV calculator |
| `irr_calculator` | IRR calculator |
| `break_even_analyzer` | Break-even analysis |
| `cash_flow_analyzer` | Cash flow analysis |
| `profit_margin` | Profit margin |
| `markup_calculator` | Markup calculator |
| `discount_calculator` | Discount calculator |
| `tax_estimator` | Tax estimator |
| `salary_paycheck_calculator` | Salary calculator |
| `sales_tax` | Sales tax |
| `tip_calculator` | Tip calculator |
| `depreciation_calculator` | Depreciation |
| `inventory_turnover` | Inventory turnover |
| `customer_acquisition_cost` | CAC |
| `customer_lifetime_value` | CLV |
| `burn_rate_calculator` | Burn rate |
| `working_capital_calculator` | Working capital |
| `debt_to_income_ratio` | DTI ratio |
| `payback_period` | Payback period |
| `dividend_yield_calculator` | Dividend yield |
| `stock_return_calculator` | Stock returns |
| `weighted_average_cost_of_capital` | WACC |
| `black_scholes_option_pricer` | Black-Scholes |

### Science & Engineering
| Skill | Description |
|-------|-------------|
| `chemistry_calculator` | Chemistry calculator |
| `molecular_weight_calculator` | Molecular weight |
| `physics_calculator` | Physics calculator |
| `ohms_law` | Ohm's law |
| `thermodynamics_calculator` | Thermodynamics |
| `fluid_dynamics_calculator` | Fluid dynamics |
| `ideal_gas_law_calculator` | Ideal gas law |
| `kinematic_solver` | Kinematics |
| `electronics_calculator` | Electronics |
| `signal_processing_fft` | FFT signal processing |
| `structural_beam_calculator` | Structural beam |
| `bearing_calculator` | Bearing calculator |
| `magnetic_declination` | Magnetic declination |
| `radioactive_decay_calculator` | Radioactive decay |
| `astronomy_calculator` | Astronomy |
| `moon_phase_calculator` | Moon phases |
| `sun_position_calculator` | Sun position |
| `periodic_table_lookup` | Periodic table |

### Text & Language
| Skill | Description |
|-------|-------------|
| `translator` | Translation (local) |
| `offline_translator` | Offline translation |
| `grammar_checker` | Grammar checking |
| `sentiment_analyzer` | Sentiment analysis |
| `text_summarizer` | Text summarization |
| `summarizer` | Content summarization |
| `readability_scorer` | Readability scoring |
| `text_classifier` | Text classification |
| `language_detector` | Language detection |
| `keyword_extractor` | Keyword extraction |
| `word_counter` | Word counter |
| `word_frequency` | Word frequency |
| `char_freq` | Character frequency |
| `sentence_splitter` | Sentence splitting |
| `tokenizer` | Text tokenization |
| `stemmer` | Word stemming |
| `lemmatizer` | Word lemmatization |
| `stopword_remover` | Stopword removal |
| `n_gram_generator` | N-gram generation |
| `rhyme_finder` | Rhyme finder |
| `syllable_counter` | Syllable counter |
| `haiku_generator` | Haiku generation |
| `limerick_generator` | Limerick generation |
| `lorem_ipsum` | Lorem ipsum |
| `pig_latin` | Pig Latin |
| `leetspeak` | Leetspeak |
| `morse_code` | Morse code |
| `emoji_translator` | Emoji translation |

### Crypto & Encoding
| Skill | Description |
|-------|-------------|
| `base64_codec` | Base64 encode/decode |
| `base32_encoder` | Base32 encoder |
| `hex_to_binary` | Hex to binary |
| `binary_converter` | Binary converter |
| `base_converter` | Base converter |
| `caesar_cipher` | Caesar cipher |
| `rot13` | ROT13 cipher |
| `vigenere_cipher` | Vigenère cipher |
| `xor_cipher` | XOR cipher |
| `hash_generator` | Hash generator |
| `sha256_checksum` | SHA256 checksum |
| `md5_checksum` | MD5 checksum |
| `crc32_checksum` | CRC32 checksum |
| `jwt_decoder` | JWT decoder |
| `key_derivation` | Key derivation |

### System & Monitoring
| Skill | Description |
|-------|-------------|
| `system_monitor` | System monitoring |
| `system_info_collector` | System info |
| `cpu_usage_monitor` | CPU usage |
| `memory_usage_analyzer` | Memory usage |
| `disk_usage` | Disk usage |
| `disk_usage_analyzer` | Disk analysis |
| `network_interface_info` | Network info |
| `process_list` | Process list |
| `service_status` | Service status |
| `system_load_analyzer` | System load |
| `temp_file_manager` | Temp file management |
| `file_finder` | File finder |
| `file_comparator` | File comparison |
| `file_hasher` | File hashing |
| `file_metadata_reader` | File metadata |
| `file_permission_checker` | File permissions |
| `duplicate_file_finder` | Duplicate finder |
| `directory_tree` | Directory tree |
| `file_archiver_zip` | ZIP archiver |
| `file_converter` | File converter |

### Utilities (100+ more)
| Skill | Description |
|-------|-------------|
| `qr_code_generator` | QR code generation |
| `barcode_generator` | Barcode generation |
| `barcode_validator` | Barcode validation |
| `uuid_generator` | UUID generation |
| `password_generator` | Password generation |
| `random_generator` | Random generation |
| `unit_converter` | Unit conversion |
| `temperature_converter` | Temperature |
| `timezone_converter` | Timezone |
| `currency_converter_static` | Currency |
| `color_converter` | Color conversion |
| `regex_tester` | Regex testing |
| `cron_parser` | Cron parsing |
| `semver_parser` | Semver parsing |
| `iban_validator` | IBAN validation |
| `isbn_validator` | ISBN validation |
| `credit_card_validator` | Credit card validation |
| `prime_checker` | Prime checking |
| `fibonacci_gen` | Fibonacci generator |
| `collatz` | Collatz conjecture |
| ...and 200+ more utilities |

---

## REST API

EvolvixOS exposes **800+ REST API endpoints** across all skills. Start the API server:

```bash
python main.py --api    # API on http://localhost:5001
```

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat` | Chat with EvolvixOS |
| POST | `/api/v1/chat/stream` | Streaming chat (SSE) |
| GET | `/api/v1/status` | System status |
| GET | `/api/v1/memory` | Search memory |
| POST | `/api/v1/voice` | Speech-to-text |
| POST | `/api/v1/speak` | Text-to-speech |

### Project Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/project/load` | Load a project for analysis |
| POST | `/api/v1/project/ask` | Ask about a loaded project |
| GET | `/api/v1/project/list` | List loaded projects |
| POST | `/api/v1/project/represent` | Represent a project |

### Genie (Zero-Code Builder)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/genie` | Build from natural language |
| POST | `/api/v1/genie/understand` | Parse intent without building |

### Sub-Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/agents/spawn` | Spawn a sub-agent |
| POST | `/api/v1/agents/run` | Run parallel agents |
| GET | `/api/v1/agents` | List active agents |
| GET | `/api/v1/agents/{id}` | Get agent status |
| GET | `/api/v1/agents/{id}/result` | Get agent result |
| DELETE | `/api/v1/agents/{id}` | Stop an agent |

### Universal API Manager

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/apis/register` | Register an external API |
| GET | `/api/v1/apis` | List registered APIs |
| POST | `/api/v1/apis/{name}/call` | Call an API endpoint |
| GET | `/api/v1/apis/{name}/health` | Check API health |
| POST | `/api/v1/apis/chain` | Chain API calls |

### VoIP Calls

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/voip/setup` | Set up VoIP provider |
| POST | `/api/v1/voip/call` | Make outbound call |
| POST | `/api/v1/voip/answer` | Answer incoming call |
| POST | `/api/v1/voip/sms` | Send SMS |
| POST | `/api/v1/voip/voicemail` | Transcribe voicemail |
| GET | `/api/v1/voip/history` | Call history |
| POST | `/api/v1/voip/ivr` | Create IVR menu |

### Device Connector

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/devices` | List devices |
| POST | `/api/v1/devices/register` | Register a device |
| POST | `/api/v1/devices/{id}/control` | Control a device |
| GET | `/api/v1/devices/{id}/status` | Get device status |
| GET | `/api/v1/devices/discover` | Discover devices |
| POST | `/api/v1/devices/bridge` | Set up platform bridge |
| DELETE | `/api/v1/devices/{id}` | Remove device |

### Life Manager

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/life/tasks` | List/add tasks |
| POST | `/api/v1/life/tasks/{id}/complete` | Complete task |
| GET/POST | `/api/v1/life/events` | List/add events |
| GET/POST | `/api/v1/life/contacts` | List/add contacts |
| GET/POST | `/api/v1/life/expenses` | List/add expenses |
| GET/POST | `/api/v1/life/goals` | List/add goals |
| GET/POST | `/api/v1/life/shopping` | List/add shopping |
| GET/POST | `/api/v1/life/reminders` | List/add reminders |
| GET | `/api/v1/life/summary` | Daily briefing |
| GET | `/api/v1/life/suggest` | AI suggestions |

### GitHub Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/discover` | Discover skills on GitHub |
| POST | `/api/v1/discover/auto` | Auto-discover & learn |
| GET | `/api/v1/catalog` | Show skill catalog |
| POST | `/api/v1/skills/{name}` | Run a specific skill |

### Python SDK

Drop `evolvix_client.py` into any project:

```python
from evolvix_client import EvolvixClient

evolvix = EvolvixClient("http://localhost:5001")

# Chat
response = evolvix.chat("Explain how neural networks work")

# Build with Genie
project = evolvix.genie("I need a website for my bakery")

# Load a project
evolvix.load_project("/path/to/your/app", name="MyApp")
evolvix.represent("MyApp")

# Voice
text = evolvix.speech_to_text("recording.wav")
evolvix.save_speech("Hello!", "output.wav")

# Life management
evolvix.add_task("Buy groceries", priority="high")
evolvix.add_event("Team meeting", "2026-08-15T10:00:00")
evolvix.get_summary()  # Morning briefing
```

---

## Architecture

```
EvolvixOS/
├── agent/                  # Core AI brain (Ollama, zero tokens)
│   ├── core.py             # Think → Plan → Act → Observe → Reflect
│   ├── memory.py           # Local SQLite memory
│   └── planner.py          # Task decomposition
├── skills/                 # 439+ modular capabilities (all local)
│   ├── genie/              # Zero-code natural language builder
│   ├── sub_agents/         # Parallel AI workers
│   ├── github_discovery/   # GitHub skill discovery & learning
│   ├── self_improver/      # Self-improvement engine
│   ├── voip_calls/         # Phone call answering
│   ├── life_manager/       # Real life management
│   ├── device_connector/   # Any device/app connection
│   ├── api_manager/        # External API management
│   ├── auto_auditor/       # Security auditing
│   ├── auto_fixer/         # Automatic code fixes
│   ├── coding/             # Code generation
│   ├── research/           # Web research
│   ├── video/              # Video generation
│   ├── image/              # Image generation
│   ├── voice/              # Voice (Whisper + Kokoro)
│   ├── project_learner/    # Codebase learning
│   ├── deploy/             # Server deployment
│   ├── hetzner_server/     # Hetzner cloud management
│   ├── model_registry/    # ML model registry
│   ├── experiment_tracker/ # ML experiment tracking
│   ├── pipeline_builder/   # ML pipeline building
│   ├── pipeline_engine/    # ML pipeline execution
│   └── [430 more skills]   # All local, all free
├── templates/              # 11,000+ project templates
├── platform/               # AI Engineering Platform
│   ├── dashboard.py        # Platform dashboard
│   ├── websocket_server.py # Real-time updates
│   ├── registry.py         # Model registry
│   └── orchestrator.py     # Pipeline orchestration
├── api_server.py           # REST API (800+ endpoints)
├── evolvix_client.py       # Python SDK client
├── discover_skills.py     # GitHub discovery CLI
├── main.py                 # Entry point
├── benchmark.py            # System benchmarks (490 checks)
├── tests/                  # Test suite (186 tests)
├── deploy/                 # Production deployment
│   ├── deploy.sh           # One-command deployment
│   ├── docker-compose.yml  # Docker Compose config
│   ├── Dockerfile          # Container definition
│   ├── nginx.conf          # Nginx reverse proxy
│   └── DOMAIN_SETUP.md     # DNS/SSL guide
├── docs/                   # Documentation & GitHub Pages
│   └── index.html          # Landing page
├── config/
│   └── config.yaml         # All settings
├── data/                   # Local data storage
├── output/                 # Generated projects
└── logs/                   # System logs
```

### How GitHub Learning Works

```
EvolvixOS GitHub Discovery Engine
┌─────────────────────────────────────────────────┐
│                                                 │
│  1. DISCOVER  → Searches GitHub API for all     │
│                 open-source AI tools            │
│                 (50+ topics searched)            │
│                                                 │
│  2. INSTALL   → Clones top repos locally        │
│                 (zero tokens, just git clone)    │
│                                                 │
│  3. LEARN     → Local LLM studies each tool's   │
│                 code and learns when/how to use  │
│                                                 │
│  4. USE       → Agent invokes any learned skill │
│                 in its workflow                  │
│                                                 │
│  5. UPDATE    → Periodically pulls updates from │
│                 GitHub for installed skills      │
│                                                 │
│  Result: EvolvixOS gets smarter every day       │
│          without spending a single token         │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) (for local LLM)
- 8GB+ RAM (16GB+ recommended)
- GPU optional (but faster for AI tasks)

### Installation

```bash
# Clone
git clone https://github.com/Protremix/EvolvixOS.git
cd EvolvixOS

# Install (one-time)
./setup.sh

# Pull local AI models
ollama pull deepseek-r1:7b
ollama pull qwen2.5-coder:7b
ollama pull llama3.2:3b
```

### Usage

```bash
# Interactive chat
python main.py

# API server (800+ endpoints)
python main.py --api

# Web UI
python main.py --web

# Voice interaction (local Whisper + Kokoro)
python main.py --voice

# Learn a specific codebase
python main.py --project ./myapp

# Discover & learn from GitHub AI skills
python main.py --discover --auto

# Run benchmarks
python benchmark.py
```

### GitHub Skill Discovery

```bash
# Search GitHub for all open-source AI skills
python discover_skills.py discover

# Auto-install top skills (100+ stars)
python discover_skills.py install_all

# Learn how to use all installed skills
python discover_skills.py learn_all

# Full autonomous cycle: discover → install → learn
python discover_skills.py auto

# Show catalog of all discovered/installed/learned skills
python discover_skills.py catalog

# Update all installed skills from GitHub
python discover_skills.py update
```

---

## Deployment

### One-Command Deployment

Deploy EvolvixOS to any server with GPU:

```bash
# 1. Point DNS to your server
#    A record: evolvixos.com → your server IP
#    A record: www.evolvixos.com → your server IP

# 2. Deploy (one command)
./deploy/deploy.sh root@your-server-ip --domain evolvixos.com

# 3. That's it. EvolvixOS is live.
```

### What gets deployed:

| Container | Port | Description |
|-----------|------|-------------|
| `evolvix-ollama` | 11434 | Local LLM engine (deepseek-r1, qwen2.5-coder, llama3.2) |
| `evolvix-core` | 5001 | API server (800+ endpoints) |
| `evolvix-core` | 5000 | Web UI & dashboard |
| `evolvix-nginx` | 80/443 | Reverse proxy with SSL |
| `evolvix-learner` | — | Continuous GitHub Discovery (24h cycle) |

### Docker Compose:

```bash
# Start everything
docker compose -f deploy/docker-compose.yml up -d --build

# View logs
docker logs evolvix-core -f       # API server
docker logs evolvix-learner -f   # Auto-learning

# Update from GitHub
git pull && docker compose -f deploy/docker-compose.yml up -d --build

# Check status
curl http://evolvixos.com/api/v1/status
```

### Server requirements:

- **GPU**: NVIDIA RTX 3060+ (for local AI)
- **RAM**: 32 GB recommended
- **Disk**: 50-100 GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Docker**: Auto-installed by deploy script

See [`deploy/DOMAIN_SETUP.md`](deploy/DOMAIN_SETUP.md) for full DNS/SSL configuration.

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run benchmarks (490 checks)
python benchmark.py

# Verify all skills
python -c "
import os
skills = [d for d in os.listdir('skills') if os.path.isdir(f'skills/{d}')]
print(f'{len(skills)} skills found')
"
```

**Results:**
- ✅ 186/186 tests passed
- ✅ 490/490 benchmark checks passed
- ✅ 439+ skills verified
- ✅ 11,000+ templates available
- ✅ 800+ API endpoints
- ✅ $0.00 total cost

---

## Philosophy

> EvolvixOS belongs to no corporation. It runs on your machine, learns from your projects, speaks with your voice, discovers tools from the entire open-source community on GitHub, answers your phone calls, manages your real life, and never sends a single token to anyone.

**No ads. No marketing. No subscriptions. No BS.**

We don't spend money on ads or marketing. We don't have a sales team. We don't have investors to please. We just build the best AI platform possible, give it away for free, and let it speak for itself.

**Build free. Teach him. Enjoy.**

---

## License

MIT — do whatever you want with it.

---

<div align="center">

**EvolvixOS** — The AI that belongs to you.

[GitHub](https://github.com/Protremix/EvolvixOS) · [Website](https://protremix.github.io/EvolvixOS/) · [Issues](https://github.com/Protremix/EvolvixOS/issues)

*439+ skills · 11K templates · 800+ API endpoints · Zero-code builder · Real life AI · $0.00 forever*

</div>
