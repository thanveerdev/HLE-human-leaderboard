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

echo "==> Loading HF_TOKEN from hle_pipeline/.env if present"
# Load HF_TOKEN from local .env if present
if [ -f "hle_pipeline/.env" ]; then
  echo "==> Found HF_TOKEN in hle_pipeline/.env"
  set -a
  # shellcheck disable=SC1091
  . ./hle_pipeline/.env
  set +a
fi

echo "==> Initializing database (HF_TOKEN respected if set)"
if [ "$FORCE_FLAG" = "--force" ]; then
  python -m hle_pipeline.scripts.init_db --force
else
  python -m hle_pipeline.scripts.init_db
fi

echo "==> Checking mcp_server/.env"
if [ ! -f "mcp_server/.env" ]; then
  if [ -f "mcp_server/.env.example" ]; then
    cp mcp_server/.env.example mcp_server/.env
    echo "Created mcp_server/.env from .env.example. Please edit AUTH_TOKEN and MY_NUMBER."
  else
    cat > mcp_server/.env <<'EOF'
AUTH_TOKEN=change_me
MY_NUMBER=+15551234567
# DB_PATH is optional. Defaults to ../hle_pipeline/data/hle_quiz.db
# DB_PATH="/absolute/path/to/hle_quiz.db"
EOF
    echo "Created mcp_server/.env. Please edit AUTH_TOKEN and MY_NUMBER."
  fi
fi

echo ""
echo "All set. Next:"
echo "- Start the server: bash scripts/run_server.sh"
echo "- Expose publicly: cloudflared tunnel --url http://localhost:8086"


