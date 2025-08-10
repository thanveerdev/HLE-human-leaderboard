## Quick Run Guide

A minimal, end-to-end setup to run the Humanity's Last Exam (HLE) WhatsApp MCP quiz locally and connect it through a public URL.

### Prerequisites
- Python 3.11+
- `uv` package manager installed
- macOS Homebrew (for Cloudflare Tunnel)
- Hugging Face account with access granted to `cais/hle` dataset

### 1) One-command setup
This creates `hle_pipeline/data/hle_quiz.db` (if HF_TOKEN set), installs deps, and prepares env.

```bash
# From repo root
# Option A: auto-load from root .env
echo 'HF_TOKEN=hf_xxx' > .env
bash scripts/setup.sh --force

# Option B: set for this run only
HF_TOKEN=hf_xxx bash scripts/setup.sh --force
```

### 2) Run the MCP server
Start the Bearer-auth MCP server that serves questions from the SQLite DB.

```bash
bash scripts/run_server.sh
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
- Token: the value of `AUTH_TOKEN` from `.env`

After connecting, the following tools are available:

Note: If you use zsh, quote the extras like '.[server]' or escape brackets.
- `validate()` → returns your `MY_NUMBER`
- `play_exam(subject?, question_type?)` → returns one random question
- `check_answer(question_id, answer)` → verifies an answer

### Common issues
- Missing `AUTH_TOKEN` → create `.env` with `AUTH_TOKEN` and `MY_NUMBER`.
- Empty DB / no questions → ensure `HF_TOKEN` is set and re-run `init_db.py --force`.
- Custom DB location → set `DB_PATH` in `.env`.
- Cloudflare URL unreachable → keep `cloudflared` running; check local firewall.
- `.env` parsing errors → only `KEY=VALUE` lines; quote paths with spaces.

That’s it—your WhatsApp MCP quiz is live in minutes.


