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

Requirements: Python 3.11+, `uv` installed. If `hle_pipeline/.env` exists with `HF_TOKEN=...`, setup will auto-load it.

```bash
## Option A: Use local env file
echo 'HF_TOKEN=hf_xxx' > hle_pipeline/.env
bash scripts/setup.sh --force

## Option B: Export in shell for this run
HF_TOKEN=hf_xxx bash scripts/setup.sh --force
```

This will create venvs, install deps via uv, initialize the DB, and prepare `mcp_server/.env`.

### 2) Run the MCP server

```bash
bash scripts/run_server.sh
```

You should see the MCP server listening on http://0.0.0.0:8086.

Note for zsh users: always quote extras, e.g. '.[server]' or escape brackets: .\[server\].

### 3) Expose the MCP server (Cloudflare Tunnel)

```bash
# Install once (macOS):
brew install cloudflare/cloudflare/cloudflared

# Start a quick tunnel to your local MCP server
cloudflared tunnel --url http://localhost:8086
```
#cloudflared tunnel --edge-ip-version 4 --protocol quic --logfile logs/cloudflared.log --loglevel debug --url http://localhost:8086 // for edgecases

Copy the printed `https://<random>.trycloudflare.com` URL.

### 4) Connect in your WhatsApp host (MCP client)
- Endpoint: your Cloudflare URL
- Auth type: Bearer
- Token: the value of `AUTH_TOKEN` in mcp_server/.env

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

- Secrets
  - MCP: `mcp_server/.env` with `AUTH_TOKEN`, `MY_NUMBER` (E.164 format).
  - HLE ingest: `hle_pipeline` with `HF_TOKEN` exported in your shell (or via a local .env if you integrate it).
- Database path
  - Defaults to `../hle_pipeline/data/hle_quiz.db` from `mcp_server/`.
  - Override by setting `DB_PATH` in `mcp_server/.env`.
- Cloud exposure
  - `cloudflared tunnel --url http://localhost:8086` is the fastest path for demos.
- Licensing
  - HLE code is MIT (repo); dataset terms apply via Hugging Face. Do not train on HLE; respect redistribution limits.

## Troubleshooting

- MCP server fails with `AUTH_TOKEN is required`:
  - Create `mcp_server/.env` with `AUTH_TOKEN=...` and `MY_NUMBER=+...` (no quotes or comments).
- `python-dotenv could not parse statement ...`:
  - Ensure `.env` contains only `KEY=VALUE` lines; wrap DB paths with spaces in double quotes.
- `No question available for provided filters`:
  - Remove filters or verify the DB is populated (re-run `scripts/init_db.py --force`).
- Cloudflare URL not reachable:
  - Keep `cloudflared` running; confirm your local firewall allows the port.

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
