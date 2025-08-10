import asyncio
import os
import sqlite3
from typing import Annotated, Optional, List

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp.server.auth.provider import AccessToken
from mcp.types import INVALID_PARAMS
from mcp import ErrorData, McpError
from pydantic import BaseModel, Field

# Load env
load_dotenv()

AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER", "")  # optional

# Default DB path: ../HLE-Streamlit/data/hle_quiz.db relative to this file
DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../HLE-Streamlit/data/hle_quiz.db")
)
DB_PATH = os.environ.get("DB_PATH", DEFAULT_DB_PATH)

if not AUTH_TOKEN:
    raise RuntimeError("AUTH_TOKEN is required in environment (.env)")

class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(token=token, client_id="puch-client", scopes=["*"], expires_at=None)
        return None

mcp = FastMCP(
    "HLE Quiz MCP Server",
    auth=SimpleBearerAuthProvider(AUTH_TOKEN),
)

# DB helpers

def get_conn() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"DB not found at {DB_PATH}. Run scripts/init_db.py first."))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class Question(BaseModel):
    id: str
    question: str
    subject: str
    difficulty: Optional[str] = None
    question_type: Optional[str] = None


def get_all_subjects(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute("SELECT DISTINCT subject FROM questions ORDER BY subject")
    return [r[0] for r in cur.fetchall()]


def get_all_question_types(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute("SELECT DISTINCT question_type FROM questions ORDER BY question_type")
    return [r[0] for r in cur.fetchall()]


def normalize_subject(user_subject: Optional[str], available: List[str]) -> Optional[str]:
    if not user_subject:
        return None
    s = user_subject.strip().lower()
    if not s:
        return None
    # Simple synonym map
    synonyms = {
        "maths": "math",
        "mathematics": "math",
        "bio": "biology",
        "chem": "chemistry",
        "cs": "cs/ai",
        "ai": "cs/ai",
        "comp sci": "cs/ai",
    }
    s = synonyms.get(s, s)
    # Case-insensitive partial match
    for subj in available:
        subj_l = (subj or "").lower()
        if s == subj_l or s in subj_l or subj_l in s:
            return subj
    return None


def normalize_qtype(user_qtype: Optional[str], available: List[str]) -> Optional[str]:
    if not user_qtype:
        return None
    q = user_qtype.strip().lower()
    if not q:
        return None
    # Map common phrases
    if q in {"mcq", "mcqs", "multiple choice", "multiple-choice", "choice"}:
        # Most HLE entries in this app are stored as 'text'
        q = "text"
    for qt in available:
        qt_l = (qt or "").lower()
        if q == qt_l or q in qt_l or qt_l in q:
            return qt
    return None

@mcp.tool
async def validate() -> str:
    """Required by host to verify server ownership."""
    return MY_NUMBER

@mcp.tool(description="Start playing Humanity's Last Exam: returns a random question. Use when user says 'play exam'.")
async def play_exam(
    subject: Annotated[Optional[str], Field(description="Optional subject filter (e.g., Physics)")] = None,
    question_type: Annotated[Optional[str], Field(description="Optional question type filter")] = None,
) -> Question:
    # Fetch one random question from DB with optional filters (forgiving matching)
    with get_conn() as conn:
        subjects = get_all_subjects(conn)
        qtypes = get_all_question_types(conn)

        subj_canon = normalize_subject(subject, subjects)
        qtype_canon = normalize_qtype(question_type, qtypes)

        sql = "SELECT id, question, subject, difficulty, question_type FROM questions WHERE 1=1"
        params: list = []
        if subj_canon:
            sql += " AND subject = ?"
            params.append(subj_canon)
        if qtype_canon:
            sql += " AND question_type = ?"
            params.append(qtype_canon)
        sql += " ORDER BY RANDOM() LIMIT 1"

        cur = conn.execute(sql, params)
        row = cur.fetchone()
        if not row:
            # Fallback: ignore filters entirely
            cur = conn.execute(
                "SELECT id, question, subject, difficulty, question_type FROM questions ORDER BY RANDOM() LIMIT 1"
            )
            row = cur.fetchone()
        if not row:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="No question available (database empty)"))
        return Question(**dict(row))

@mcp.tool(description="Check an answer for a question id. Returns whether correct and the ground truth.")
async def check_answer(
    question_id: Annotated[str, Field(description="The question id returned by play_exam")],
    answer: Annotated[str, Field(description="User's answer text")],
) -> str:
    answer = (answer or "").strip().lower()
    if not answer:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Answer cannot be empty"))
    with get_conn() as conn:
        cur = conn.execute("SELECT answer, explanation FROM questions WHERE id = ?", (question_id,))
        row = cur.fetchone()
        if not row:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="Unknown question id"))
        gt = (row["answer"] or "").strip().lower()
        is_correct = (answer == gt) or (gt in answer) or (answer in gt)
        expl = row["explanation"] or ""
        return (
            f"correct={str(is_correct).lower()}\n"
            f"ground_truth={row['answer']}\n"
            f"explanation={expl}"
        )

async def main():
    print(f"🚀 HLE MCP on http://0.0.0.0:8086  (DB: {DB_PATH})")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())
