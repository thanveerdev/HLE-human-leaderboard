#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT_DIR"

# Load environment variables from mcp_server/.env if it exists
if [ -f "mcp_server/.env" ]; then
  echo "==> Loading environment from mcp_server/.env"
  set -a
  source mcp_server/.env
  set +a
fi

# Run the MCP server
echo "==> Starting MCP server..."
python mcp_server/mcp_hle_server.py


