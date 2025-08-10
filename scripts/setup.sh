#!/usr/bin/env bash
set -euo pipefail

# Usage: bash scripts/setup.sh [--force]
# - Uses pip instead of uv
# - Uses HF_TOKEN from environment if set

if ! command -v python >/dev/null 2>&1; then
  echo "Error: python is not installed." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FORCE_FLAG="${1:-}"

cd "$ROOT_DIR"

echo "==> Installing package dependencies"
pip install -e ".[server,pipeline]"

echo "==> Loading env from root .env if present"
# Load variables from root .env if present
if [ -f ".env" ]; then
  echo "==> Found .env"
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

echo "==> Initializing database (HF_TOKEN respected if set)"
if [ "$FORCE_FLAG" = "--force" ]; then
  python -m hle_pipeline.scripts.init_db --force
else
  python -m hle_pipeline.scripts.init_db
fi

echo "==> Ensuring root .env exists"
if [ ! -f ".env" ]; then
  if [ -f "mcp_server/.env.example" ]; then
    cp mcp_server/.env.example .env
    echo "Created .env from mcp_server/.env.example. Please edit AUTH_TOKEN and MY_NUMBER."
  else
    cat > .env <<'EOF'
AUTH_TOKEN=change_me
MY_NUMBER=+15551234567
# DB_PATH is optional. Defaults to hle_pipeline/data/hle_quiz.db
# DB_PATH="/absolute/path/to/hle_quiz.db"
EOF
    echo "Created .env. Please edit AUTH_TOKEN and MY_NUMBER."
  fi
fi

echo ""
echo "All set. Next:"
echo "- Start the server: bash scripts/run_server.sh"
echo "- Expose publicly: cloudflared tunnel --url http://localhost:8086"


