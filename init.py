#!/usr/bin/env python3
"""
Initialize the HLE WhatsApp MCP Quiz project.

This script:
- Creates virtual environments for HLE ingest and MCP server
- Installs dependencies
- Ingests the HLE dataset into SQLite (if HF_TOKEN is available)
- Creates/updates prototype1/.env with AUTH_TOKEN and MY_NUMBER

Usage examples:
  python init.py                           # auto-setup; uses env HF_TOKEN/AUTH_TOKEN/MY_NUMBER if present
  python init.py --hf-token hf_xxx         # provide HF token to ensure ingestion
  python init.py --auth-token abc --my-number +15551234567
  python init.py --force                   # force DB refresh on ingest
  python init.py --start-server            # start MCP server at the end

Notes:
- The MCP server listens on http://0.0.0.0:8086
- Expose it via Cloudflare Tunnel:
    cloudflared tunnel --url http://localhost:8086
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import secrets
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=True)


def venv_python(venv_dir: Path) -> Path:
    if platform.system().lower().startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def ensure_uv_installed() -> None:
    if shutil.which("uv") is None:
        raise RuntimeError(
            "uv is required. Install with: brew install uv  (macOS) or see https://docs.astral.sh/uv/"
        )


def _read_env_file(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        return {}
    result: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        result[key] = value
    return result


def write_env_file(env_path: Path, auth_token: str | None, my_number: str | None, db_path: Path | None) -> None:
    # Merge with existing values; do not clobber unless explicit values provided
    existing = _read_env_file(env_path)
    merged: dict[str, str] = dict(existing)
    if auth_token:
        merged["AUTH_TOKEN"] = auth_token
    else:
        merged.setdefault("AUTH_TOKEN", secrets.token_hex(16))
    if my_number is not None and my_number != "":
        merged["MY_NUMBER"] = my_number
    else:
        # Preserve existing MY_NUMBER if present; otherwise leave empty string
        merged.setdefault("MY_NUMBER", existing.get("MY_NUMBER", ""))
    if db_path is not None:
        merged["DB_PATH"] = str(db_path)
    else:
        if "DB_PATH" in existing:
            merged["DB_PATH"] = existing["DB_PATH"]

    # Backup existing file
    if env_path.exists():
        backup = env_path.with_suffix(env_path.suffix + ".bak")
        backup.write_text(env_path.read_text(encoding="utf-8"), encoding="utf-8")

    def fmt_value(v: str) -> str:
        return f'"{v}"' if (" " in v or v.startswith("/")) else v

    lines = [
        f"AUTH_TOKEN={fmt_value(merged.get('AUTH_TOKEN', ''))}",
        f"MY_NUMBER={fmt_value(merged.get('MY_NUMBER', ''))}",
    ]
    if merged.get("DB_PATH"):
        lines.append(f"DB_PATH={fmt_value(merged['DB_PATH'])}")
    content = "\n".join(lines) + "\n"
    env_path.write_text(content, encoding="utf-8")
    print(f"Wrote {env_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize HLE WhatsApp MCP project")
    parser.add_argument("--hf-token", dest="hf_token", default=os.environ.get("HF_TOKEN"), help="Hugging Face token")
    parser.add_argument("--auth-token", dest="auth_token", default=os.environ.get("AUTH_TOKEN"), help="Bearer auth token for MCP server")
    parser.add_argument("--my-number", dest="my_number", default=os.environ.get("MY_NUMBER"), help="Your phone number in E.164 format (e.g., +15551234567)")
    parser.add_argument("--force", action="store_true", help="Force dataset refresh during ingest")
    parser.add_argument("--start-server", action="store_true", help="Start the MCP server at the end")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    hle_dir = root / "hle_pipeline"
    hle_scripts = hle_dir / "scripts"
    hle_data = hle_dir / "data"
    hle_venv = hle_dir / ".venv"
    hle_requirements = hle_dir / "quiz_requirements.txt"

    server_dir = root / "mcp_server"
    server_venv = server_dir / ".venv"
    server_requirements = server_dir / "requirements.txt"
    server_env = server_dir / ".env"

    base_python = sys.executable
    print(f"Using base python: {base_python}")

    # 1) Prepare HLE venv and ingest DB
    ensure_uv_installed()
    # Create venvs with uv (idempotent)
    if not hle_venv.exists():
        run(["uv", "venv"], cwd=hle_dir)
    hle_py = venv_python(hle_venv)
    # Prefer installing from root via extras to keep dependencies centralized
    hle_env = os.environ.copy()
    hle_env["VIRTUAL_ENV"] = str(hle_venv)
    hle_env["PATH"] = str(hle_venv / "bin") + os.pathsep + hle_env.get("PATH", "")
    run(["uv", "pip", "install", "-e", ".[pipeline]"], cwd=root, env=hle_env)

    ingest_env = os.environ.copy()
    if args.hf_token:
        ingest_env["HF_TOKEN"] = args.hf_token
        print("HF_TOKEN provided: ingestion will include HLE dataset")
    else:
        print("HF_TOKEN not provided: will initialize DB without dataset ingestion")

    init_db_cmd = [str(hle_py), str(hle_scripts / "init_db.py")]
    if args.force:
        init_db_cmd.append("--force")
    run(init_db_cmd, cwd=hle_dir, env=ingest_env)

    # 2) Prepare MCP server venv and .env
    if not server_venv.exists():
        run(["uv", "venv"], cwd=server_dir)
    server_py = venv_python(server_venv)
    server_env = os.environ.copy()
    server_env["VIRTUAL_ENV"] = str(server_venv)
    server_env["PATH"] = str(server_venv / "bin") + os.pathsep + server_env.get("PATH", "")
    run(["uv", "pip", "install", "-e", ".[server]"], cwd=root, env=server_env)

    # Preserve existing .env values unless explicitly overridden via flags/env
    existing = _read_env_file(server_env)
    auth_token = args.auth_token or existing.get("AUTH_TOKEN") or secrets.token_hex(16)
    my_number = args.my_number if args.my_number is not None else existing.get("MY_NUMBER", "")
    # Use default DB path resolution inside server; do not force DB_PATH unless absent
    db_path = None
    # If data dir exists and DB file is present, we can optionally set DB_PATH explicitly
    default_db = hle_data / "hle_quiz.db"
    if default_db.exists():
        db_path = default_db
    write_env_file(server_env, auth_token=auth_token, my_number=my_number, db_path=db_path)

    print("\nSetup complete.")
    print("\nNext steps:")
    print(f"1) Start the MCP server:\n   cd {server_dir}\n   source .venv/bin/activate\n   python mcp_hle_server.py")
    print("2) Expose publicly (in another terminal):\n   cloudflared tunnel --url http://localhost:8086")
    print("3) Connect from your WhatsApp host using Bearer auth with your AUTH_TOKEN.")

    if args.start_server:
        print("\nStarting MCP server...")
        run([str(server_py), str(server_dir / "mcp_hle_server.py")], cwd=server_dir)


if __name__ == "__main__":
    main()


