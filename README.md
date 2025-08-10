# Humanity's Last Exam – WhatsApp Quiz (MCP)

A hackathon-ready WhatsApp quiz experience powered by "Humanity's Last Exam" (HLE). This repo contains:

- A SQLite-backed dataset ingest and local API (`HLE-Streamlit/`)
- A minimal MCP server that serves questions from the DB (`prototype1/`)
- Planning docs and usage notes (`humanitys-last-exam/`)

Use your WhatsApp host that supports MCP (Model Context Protocol) to call the MCP tools and deliver the quiz in chat.

> Note: HLE dataset distribution is via Hugging Face under gated terms. You must accept the dataset conditions before programmatic access. The HLE repo code is MIT-licensed; the dataset has its own terms.

## Repository structure

```
/ (root)
├─ HLE-Streamlit/             # Dataset ingestion + optional local API + Streamlit demo
│  ├─ core/                   # SQLite schema & ingestion logic
│  ├─ scripts/                # init_db.py (creates and populates SQLite DB)
│  ├─ api/                    # FastAPI server serving questions from DB
│  ├─ app/                    # Streamlit demo app (optional)
│  └─ data/hle_quiz.db        # SQLite DB (created on first ingest)
├─ prototype1/                # Minimal MCP server (Bearer auth)
│  ├─ mcp_hle_server.py       # MCP tools: validate, play_exam, check_answer
│  ├─ requirements.txt        # Minimal deps
│  └─ .env.example            # Copy to .env and fill AUTH_TOKEN, MY_NUMBER
└─ humanitys-last-exam/       # Plans and notes
```

## Quick start

### 1) Create and populate the SQLite database (HLE)

Requirements: Python 3.11+, access to `cais/hle` on Hugging Face, and an HF token.

```bash
cd "HLE-Streamlit"
python3 -m venv .venv
. .venv/bin/activate
pip install -r quiz_requirements.txt

# Set your HF token (must have accepted the dataset terms)
export HF_TOKEN=hf_xxx
python scripts/init_db.py --force
```

On success, `data/hle_quiz.db` will contain the questions.

Optional: run the local API for debugging/UI
```bash
uvicorn api.api_server:app --host 0.0.0.0 --port 8000
```

### 2) Run the MCP server

```bash
cd "../prototype1"
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

# Create .env from example and set your values
cp .env.example .env
# Edit .env and set:
# AUTH_TOKEN=supersecret123
# MY_NUMBER=+<your_e164_number>
# (DB_PATH is optional; defaults to ../HLE-Streamlit/data/hle_quiz.db)

python mcp_hle_server.py
```

You should see the MCP server listening on http://0.0.0.0:8086.

### 3) Expose the MCP server (Cloudflare Tunnel)

```bash
# Install once (macOS):
brew install cloudflare/cloudflare/cloudflared

# Start a quick tunnel to your local MCP server
cloudflared tunnel --url http://localhost:8086
```

Copy the printed `https://<random>.trycloudflare.com` URL.

### 4) Connect in your WhatsApp host (MCP client)
- Endpoint: your Cloudflare URL
- Auth type: Bearer
- Token: the value of `AUTH_TOKEN` in prototype1/.env

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
  - MCP: `prototype1/.env` with `AUTH_TOKEN`, `MY_NUMBER` (E.164 format).
  - HLE ingest: `HLE-Streamlit` with `HF_TOKEN` exported in your shell (or via a local .env if you integrate it).
- Database path
  - Defaults to `../HLE-Streamlit/data/hle_quiz.db` from `prototype1/`.
  - Override by setting `DB_PATH` in `prototype1/.env`.
- Cloud exposure
  - `cloudflared tunnel --url http://localhost:8086` is the fastest path for demos.
- Licensing
  - HLE code is MIT (repo); dataset terms apply via Hugging Face. Do not train on HLE; respect redistribution limits.

## Troubleshooting

- MCP server fails with `AUTH_TOKEN is required`:
  - Create `prototype1/.env` with `AUTH_TOKEN=...` and `MY_NUMBER=+...` (no quotes or comments).
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
