#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT_DIR/mcp_server"
if [ ! -d .venv ]; then
  echo "mcp_server venv not found. Run: bash scripts/setup.sh" >&2
  exit 1
fi

export VIRTUAL_ENV="$PWD/.venv"
export PATH="$VIRTUAL_ENV/bin:$PATH"

exec "$VIRTUAL_ENV/bin/python" mcp_hle_server.py


