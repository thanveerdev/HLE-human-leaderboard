#!/usr/bin/env bash
set -euo pipefail

# Usage: bash scripts/setup.sh [--force]
# - Expects `uv` to be installed
# - Uses HF_TOKEN from environment if set

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is not installed. Install with: brew install uv (macOS) or see https://docs.astral.sh/uv/" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FORCE_FLAG="${1:-}"

echo "==> Setting up hle_pipeline"
pushd "$ROOT_DIR/hle_pipeline" >/dev/null
if [ ! -d .venv ]; then
  uv venv
fi
# Load HF_TOKEN from local .env if present
if [ -f .env ]; then
  echo "==> Loading HF_TOKEN from hle_pipeline/.env"
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi
export VIRTUAL_ENV="$PWD/.venv"
export PATH="$VIRTUAL_ENV/bin:$PATH"
uv pip install -e '..[pipeline]'
echo "==> Initializing database (HF_TOKEN respected if set)"
if [ "$FORCE_FLAG" = "--force" ]; then
  "$VIRTUAL_ENV/bin/python" scripts/init_db.py --force
else
  "$VIRTUAL_ENV/bin/python" scripts/init_db.py
fi
popd >/dev/null

echo "==> Setting up mcp_server"
pushd "$ROOT_DIR/mcp_server" >/dev/null
if [ ! -d .venv ]; then
  uv venv
fi
export VIRTUAL_ENV="$PWD/.venv"
export PATH="$VIRTUAL_ENV/bin:$PATH"
uv pip install -e '..[server]'

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "Created mcp_server/.env from .env.example. Please edit AUTH_TOKEN and MY_NUMBER."
  else
    cat > .env <<'EOF'
AUTH_TOKEN=change_me
MY_NUMBER=+15551234567
# DB_PATH is optional. Defaults to ../hle_pipeline/data/hle_quiz.db
# DB_PATH="/absolute/path/to/hle_quiz.db"
EOF
    echo "Created mcp_server/.env. Please edit AUTH_TOKEN and MY_NUMBER."
  fi
fi
popd >/dev/null

echo "\nAll set. Next:"
echo "- Start the server: bash scripts/run_server.sh"
echo "- Expose publicly: cloudflared tunnel --url http://localhost:8086"


