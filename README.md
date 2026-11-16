# Customer Service Agent

A production-style customer service AI agent built with
[Strands Agents](https://strandsagents.com) and deployable to
[Amazon Bedrock AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/).

This repository contains a standalone, config-driven Python package that brings
the agent loop, tools, skills, guardrails, memory, delegation, and evaluations
together in one deployable application.

## What's included

| Capability | Where |
|------------|-------|
| Agent loop + customer tools (lookup, orders, refunds) | `agents/customer_service.py`, `tools/customer_service.py` |
| Deterministic tool rate limiting (hooks) | `hooks/rate_limiter.py` |
| Workflow skills (refund, order tracking, account help) | `skills/` |
| Steering guardrails (refund ordering, tone) | `steering/handlers.py` |
| Persistent session memory | `session.py` |
| Multi-agent delegation (tech support specialist) | `agents/tech_support.py` |
| Automated evals (output + trajectory) | `evals/` |
| AgentCore Runtime entrypoint | `runtime.py` |
| Interactive CLI | `cli.py` |

## Install

```bash
cd customer-service-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Optional: evaluations and local Ollama support
pip install -e '.[evals,ollama]'
```

Configure AWS credentials with access to Amazon Bedrock (default region
`us-east-1`), or run locally with Ollama:

```bash
cp .env.example .env
# set CS_AGENT_MODEL_PROVIDER=ollama and pull a tool-capable model:
ollama pull llama3.1
```

## Run

```bash
# Interactive chat (persists sessions under ./sessions)
csa chat

# Resume a named conversation
csa chat --session-id customer-session-001

# Try a configuration without persistent memory
csa chat --no-session

# Run automated evaluations
csa eval            # both suites
csa eval --which output
csa eval --which trajectory

# Serve the AgentCore Runtime entrypoint locally
csa serve
```

Example conversation:

```text
You: Hi, I'm customer C-1001. What are my recent orders?
You: My wireless headphones won't pair with my phone.
You: I'd like a refund for order ORD-5521.
```

## Configuration

All settings can be supplied via environment variables (see `.env.example`) or
CLI flags. Feature flags let you enable just the capabilities you need:

| Variable | Default | Purpose |
|----------|---------|---------|
| `CS_AGENT_MODEL_PROVIDER` | `bedrock` | `bedrock`, `nova`, `ollama`, `llama`, or `openai` |
| `CS_AGENT_MODEL_ID` | Provider default | Explicit model id |
| `GEMINI_API_KEY` | none | API key for the `gemini` provider |
| `OLLAMA_API_KEY` | none | API key for Ollama Cloud |
| `CS_AGENT_OLLAMA_HOST` | `http://localhost:11434` | Ollama host (`https://ollama.com` for Cloud) |
| `LLAMA_API_KEY` | none | API key for `llama` / `openai` providers |
| `CS_AGENT_BASE_URL` | `https://api.llama.com/compat/v1` | Endpoint for the `openai` provider |
| `CS_AGENT_SESSION_ID` | `customer-session-001` | Local session to persist/resume |
| `CS_AGENT_SESSION_DIR` | `./sessions` | Snapshot storage directory |
| `CS_AGENT_MAX_TOOL_CALLS` | `5` | Per-invocation tool-call cap |
| `CS_AGENT_ENABLE_SKILLS` | `true` | Load workflow skills |
| `CS_AGENT_ENABLE_STEERING` | `true` | Refund + tone guardrails |
| `CS_AGENT_ENABLE_RATE_LIMIT` | `true` | Tool rate limiter |
| `CS_AGENT_ENABLE_MULTI_AGENT` | `true` | Tech support delegation |

Model options:

- **Bedrock (default):** Claude via Amazon Bedrock, SDK default model.
- **Nova:** `CS_AGENT_MODEL_PROVIDER=nova` (AWS credits cover Nova, not Claude).
- **Gemini:** `CS_AGENT_MODEL_PROVIDER=gemini` with `GEMINI_API_KEY`.
- **Ollama (Cloud or local):** `CS_AGENT_MODEL_PROVIDER=ollama`, plus
  `CS_AGENT_OLLAMA_HOST` and `CS_AGENT_MODEL_ID`. Ollama Cloud also needs
  `OLLAMA_API_KEY`.
- **Llama API:** `CS_AGENT_MODEL_PROVIDER=llama` with `LLAMA_API_KEY`. Uses
  Strands' native `LlamaAPIModel`.
- **OpenAI-compatible Llama host:** `CS_AGENT_MODEL_PROVIDER=openai` with
  `LLAMA_API_KEY`, `CS_AGENT_BASE_URL`, and `CS_AGENT_MODEL_ID`.

## Use Gemini instead of Bedrock

Install the Gemini extra and run locally first:

```bash
pip install -e '.[gemini]'

export CS_AGENT_MODEL_PROVIDER=gemini
export CS_AGENT_MODEL_ID=gemini-3.5-flash
export GEMINI_API_KEY=your-gemini-api-key

csa chat
```

`gemini-3.5-flash` supports tool calling and is the default. If it returns
`503 UNAVAILABLE` due to demand, retry or switch to `gemini-3.6-flash`. Avoid
`gemini-2.5-flash` for new keys — Google now rejects it with `404 NOT_FOUND`.

### Alternative: Ollama

Ollama Cloud uses `https://ollama.com` and an API key; a local Ollama server
uses `http://localhost:11434` and no key.

```bash
pip install -e '.[ollama]'

# Ollama Cloud
export CS_AGENT_MODEL_PROVIDER=ollama
export CS_AGENT_OLLAMA_HOST=https://ollama.com
export CS_AGENT_MODEL_ID=gpt-oss:120b
export OLLAMA_API_KEY=your-ollama-cloud-key

# Local Ollama instead
# export CS_AGENT_OLLAMA_HOST=http://localhost:11434
# export CS_AGENT_MODEL_ID=qwen3.5:9b

csa chat
```

Ollama Cloud returns HTTP 402 when the account has no credits/subscription; add
credits at `https://ollama.com/plans`.

Use only a model that supports tool calling — this agent relies on tools,
skills, steering, and context summarization.

> `.env` is gitignored. Keep real keys there (or in your shell/secret manager),
> never in `.env.example` or source control.

## Deploy to AgentCore

The runtime entrypoint is `main.py` (`customer_service_agent.runtime:app`). Because
this project uses an external model provider and custom Python dependencies, use
the **Container** build type.

### 1. Prerequisites

```bash
# AWS credentials with AgentCore access
aws sts get-caller-identity

# Node.js 20+ and the AgentCore CLI
npm install -g @aws/agentcore@latest
agentcore --version
```

`agentcore deploy` builds the ARM64 image remotely in CodeBuild, so local
Docker/QEMU is not required.

### 2. Scaffold the project

```bash
agentcore create --name csagent --template empty --skip-install --skip-git
cd csagent
agentcore add runtime --name CustomerServiceAgent --language python \
  --network-mode PUBLIC \
  --environment-variables '{"CS_AGENT_MODEL_PROVIDER":"gemini","CS_AGENT_MODEL_ID":"gemini-3.5-flash"}'

# Store the Gemini key in AgentCore Identity (reads from a file, not inline)
agentcore add credentials api-key --name gemini --api-key file:///tmp/gemini-key

# Install the CDK dependencies used by `agentcore deploy`
npm install --prefix agentcore/cdk
```

The runtime receives `CREDENTIAL_GEMINI_NAME`; `runtime.py` fetches the key with
`@requires_api_key`. Do **not** put the key in `agentcore.json` or
`GEMINI_API_KEY` for deployed runs. `GEMINI_API_KEY` is only for the local CLI.

### 3. Install the runtime code

The deploy folder uses a flat package layout so `main.py` can import the package
without a `src` path:

```bash
mkdir -p app/CustomerServiceAgent
cp main.py .dockerignore app/CustomerServiceAgent/
cp -r src/customer_service_agent app/CustomerServiceAgent/
```

This workspace already contains the prepared `app/CustomerServiceAgent/`
(`pyproject.toml` with `where = ["."]`, `Dockerfile`, package, and skills).
Copy that folder's `pyproject.toml` and `Dockerfile` when scaffolding elsewhere.

### 4. Deploy

```bash
agentcore deploy
agentcore status
```

The first deploy also creates the CDK bootstrap stack and a CodeBuild project.
The runtime uses this configuration in `agentcore/agentcore.json`:

```json
{
  "name": "CustomerServiceAgent",
  "build": "Container",
  "entrypoint": "main.py",
  "codeLocation": "app/CustomerServiceAgent",
  "dockerfile": "Dockerfile",
  "networkMode": "PUBLIC",
  "protocol": "HTTP"
}
```

### 5. Invoke

```bash
agentcore invoke --runtime CustomerServiceAgent \
  --session-id customer-1001-session-orders-0000001 \
  --payload '{"prompt": "Hi, I am customer C-1001. What are my recent orders?"}'
```

Session IDs passed to `agentcore invoke` must be at least 33 characters. Use the
same session ID to continue a conversation.

> Gemini's free tier limits requests per day. A `429 RESOURCE_EXHAUSTED` means
> the quota for the API key is used up; wait for the reset, use another key, or
> switch `CS_AGENT_MODEL_ID`/provider and redeploy.

### 6. Human approval (steering interrupts)

When a refund needs approval, the runtime returns:

```json
{"status": "interrupted", "interrupts": [{"interruptId": "...", "name": "...", "reason": "..."}]}
```

Resume in the **same session**:

```bash
agentcore invoke --runtime CustomerServiceAgent \
  --session-id customer-1001-session-orders-0000001 \
  --payload '{"interrupt_responses": [{"interruptId": "<id>", "response": true}]}'
```

### 7. Cleanup

```bash
agentcore remove all --yes
agentcore deploy --yes
```

## Tests

```bash
pip install -e '.[dev]'
pytest
```

## Notes

- `context_manager="auto"` is used together with `SnapshotSessionManager`, which
  is compatible (unlike `FileSessionManager`/`S3SessionManager`).
- Tools are mock, in-memory implementations. Swap them for real backends in
  `tools/`.
- The agent is not configured with production credentials. Follow AWS security
  best practices before deploying.
