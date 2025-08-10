#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT_DIR"

# Load environment variables from root .env if it exists
if [ -f ".env" ]; then
  echo "==> Loading environment from .env"
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Run the MCP server
echo "==> Starting MCP server..."
python mcp_server/mcp_hle_server.py


