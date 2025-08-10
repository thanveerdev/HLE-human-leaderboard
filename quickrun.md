## Quick Run Guide

A minimal, end-to-end setup to run the Humanity's Last Exam (HLE) WhatsApp MCP quiz locally and connect it through a public URL.

### Prerequisites
- Python 3.11+
- macOS Homebrew (for Cloudflare Tunnel)
- Hugging Face account with access granted to `cais/hle` dataset

### 1) Prepare the HLE SQLite database
This step creates `HLE-Streamlit/data/hle_quiz.db` and ingests the HLE dataset.

```bash
cd "HLE-Streamlit"
python3 -m venv .venv
. .venv/bin/activate
pip install -r quiz_requirements.txt

# Required: Your HF token (accept the dataset terms first on Hugging Face)
export HF_TOKEN=hf_xxx

# Populate the SQLite DB
python scripts/init_db.py --force
```

You should now have `HLE-Streamlit/data/hle_quiz.db` populated with questions.

### 2) Run the MCP server
Start the Bearer-auth MCP server that serves questions from the SQLite DB.

```bash
cd ../prototype1
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `prototype1/` with your auth details:

```dotenv
AUTH_TOKEN=supersecret123
MY_NUMBER=+15551234567
# Optional override (default resolves to ../HLE-Streamlit/data/hle_quiz.db)
# DB_PATH="/absolute/path/to/hle_quiz.db"
```

Run the server:

```bash
python mcp_hle_server.py
```

You should see: `HLE MCP on http://0.0.0.0:8086`.

### 3) Expose the server publicly (for your WhatsApp host)
Use Cloudflare Tunnel to expose your local MCP server over HTTPS.

```bash
brew install cloudflare/cloudflare/cloudflared
cloudflared tunnel --url http://localhost:8086
```

Copy the printed `https://<random>.trycloudflare.com` URL.

### 4) Connect in your WhatsApp host (MCP client)
- Endpoint: your Cloudflare URL (from above)
- Auth type: Bearer
- Token: the value of `AUTH_TOKEN` from `prototype1/.env`

After connecting, the following tools are available:
- `validate()` → returns your `MY_NUMBER`
- `play_exam(subject?, question_type?)` → returns one random question
- `check_answer(question_id, answer)` → verifies an answer

### Common issues
- Missing `AUTH_TOKEN` → create `prototype1/.env` with `AUTH_TOKEN` and `MY_NUMBER`.
- Empty DB / no questions → ensure `HF_TOKEN` is set and re-run `init_db.py --force`.
- Custom DB location → set `DB_PATH` in `prototype1/.env`.
- Cloudflare URL unreachable → keep `cloudflared` running; check local firewall.
- `.env` parsing errors → only `KEY=VALUE` lines; quote paths with spaces.

That’s it—your WhatsApp MCP quiz is live in minutes.


