# Humanity's Last Exam – WhatsApp Quiz (MCP)

A hackathon-ready WhatsApp quiz experience powered by "Humanity's Last Exam" (HLE). This repo contains:

- A SQLite-backed dataset ingest and local API (`hle_pipeline/`)
- A minimal MCP server that serves questions from the DB (`mcp_server/`)
- Project docs (`docs/`)

Use your WhatsApp host that supports MCP (Model Context Protocol) to call the MCP tools and deliver the quiz in chat.

> Note: HLE dataset distribution is via Hugging Face under gated terms. You must accept the dataset conditions before programmatic access. The HLE repo code is MIT-licensed; the dataset has its own terms.

## Repository structure

```
/ (root)
├─ hle_pipeline/              # Dataset ingestion and SQLite DB
│  ├─ core/                   # SQLite schema & ingestion logic
│  ├─ scripts/                # init_db.py (creates and populates SQLite DB)
│  └─ data/hle_quiz.db        # SQLite DB (created on first ingest)
├─ mcp_server/                # Minimal MCP server (Bearer auth)
│  ├─ mcp_hle_server.py       # MCP tools: validate, play_exam, check_answer
│  ├─ requirements.txt        # Minimal deps
│  └─ .env.example            # Copy to .env and fill AUTH_TOKEN, MY_NUMBER
└─ docs/                      # Guides and planning docs
```

## Quick start

### 1) One-command setup

Requirements: Python 3.11+, `pip` installed. If `.env` exists with `HF_TOKEN=...`, setup will auto-load it.

```bash
## Option A: Use local env file
echo 'HF_TOKEN=hf_xxx' > .env
bash scripts/setup.sh --force

## Option B: Export in shell for this run
HF_TOKEN=hf_xxx bash scripts/setup.sh --force
```

This will install dependencies via pip, initialize the DB, and ensure a root `.env` exists.

### 2) Run the MCP server

```bash
bash scripts/run_server.sh
```

You should see the MCP server listening on http://0.0.0.0:8086.

The server will start on http://0.0.0.0:8086 and display startup information.

### 3) Expose the MCP server (Cloudflare Tunnel)

```bash
# Install cloudflared (macOS):
brew install cloudflared
# Or download directly from: https://github.com/cloudflare/cloudflared/releases

# Start a quick tunnel to your local MCP server (run in separate terminal)
cloudflared tunnel --url http://localhost:8086
```

**Note**: Keep both the MCP server and cloudflared tunnel running in separate terminal windows.

Copy the printed `https://<random>.trycloudflare.com` URL.

### 4) Connect in your WhatsApp host (MCP client)
- Endpoint: your Cloudflare URL
- Auth type: Bearer
- Token: the value of `AUTH_TOKEN` in `.env`

## Available MCP tools

- validate(): returns your `MY_NUMBER` (host uses this to verify ownership)
- play_exam(subject?, question_type?): returns one random question from the DB
- check_answer(question_id, answer): returns a simple verdict and ground truth

Example JSON response from play_exam:
```json
{
  "id": "HLE_0007",
  "question": "Which law explains ...?",
  "subject": "Physics",
  "difficulty": "Intermediate",
  "question_type": "text"
}
```

## Operational notes

- **Setup Requirements**
  - Python 3.11+ with pip installed
  - Optional: Hugging Face token for real HLE questions (otherwise uses empty database)
- **Environment Configuration**
  - MCP server: root `.env` with `AUTH_TOKEN`, `MY_NUMBER` (E.164 format)
  - HLE dataset: `HF_TOKEN` in root `.env` or `hle_pipeline/.env`
- **Database path**
  - Defaults to `hle_pipeline/data/hle_quiz.db`
  - Override by setting `DB_PATH` in root `.env`
- **Public Access**
  - Run MCP server first, then cloudflared tunnel in separate terminal
  - `cloudflared tunnel --url http://localhost:8086` provides instant public access
- Licensing
  - HLE code is MIT (repo); dataset terms apply via Hugging Face. Do not train on HLE; respect redistribution limits.

## Troubleshooting

- **MCP server fails with `AUTH_TOKEN is required`**:
  - Create root `.env` with `AUTH_TOKEN=...` and `MY_NUMBER=+...` (no quotes or comments)
- **Port 8086 already in use**:
  - Kill existing process: `lsof -ti :8086 | xargs kill -9`
  - Or change port in `mcp_hle_server.py`
- **`python-dotenv could not parse statement`**:
  - Ensure `.env` contains only `KEY=VALUE` lines; wrap paths with spaces in double quotes
- **`No question available`**:
  - Database is empty - set `HF_TOKEN` and re-run `bash scripts/setup.sh --force`
- **Cloudflare tunnel fails with "context canceled"**:
  - Ensure MCP server is fully started and listening on port 8086 before running tunnel
  - Check `curl http://localhost:8086` returns a response
- **Missing dependencies**:
  - Run `pip install -e ".[server,pipeline]"` from project root

## Roadmap (nice-to-haves)

- Multi-user sessions and scoring in MCP (Redis or Postgres)
- Adaptive testing (IRT-lite) across subjects
- Confidence-calibrated scoring and leaderboards
- Group battle mode for WhatsApp groups
- Grounded short-answer judging (retrieval + rubric)

## Acknowledgments

- Humanity's Last Exam by Center for AI Safety & collaborators
- Hugging Face for dataset hosting
- FastMCP for the MCP server framework
