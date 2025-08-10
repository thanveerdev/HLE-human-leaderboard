#!/usr/bin/env python3
"""
Initialize the SQLite database for hle_pipeline and (optionally) ingest the HLE dataset
from Hugging Face if HF_TOKEN is configured and you have access.

Usage:
  python scripts/init_db.py [--force]

Env:
  HF_TOKEN: Hugging Face token (optional; required to ingest HLE)
  DB_PATH:  Path to SQLite DB (default: data/hle_quiz.db)
"""

import os
import sys

# Ensure project root is on sys.path to import core/* when running as a script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.hle_database_loader import HLEDatabaseLoader
from core.database_manager import DatabaseManager

def main():
    force_refresh = "--force" in sys.argv
    db_path = os.environ.get("DB_PATH", "data/hle_quiz.db")

    # Ensure DB initialized
    db = DatabaseManager(db_path=db_path)
    stats = db.get_stats()
    print(f"DB at {db_path} initialized. Questions: {stats['total_questions']}")

    # Ingest HLE if possible
    loader = HLEDatabaseLoader(db_path=db_path)
    if os.environ.get("HF_TOKEN"):
        print("HF_TOKEN detected; attempting to ingest HLE dataset...")
        ok = loader.load_dataset_to_db(force_refresh=force_refresh)
        print("Ingestion status:", "success" if ok else "failed")
    else:
        print("HF_TOKEN not set; skipping HLE ingestion. You can set HF_TOKEN and rerun.")

    # Print final stats
    final = db.get_stats()
    print("Final stats:")
    print(" - total_questions:", final["total_questions"])
    print(" - subjects:", len(final["subjects"]))
    print(" - difficulties:", len(final["difficulties"]))
    print(" - question_types:", len(final.get("question_types", [])))

if __name__ == "__main__":
    main()
