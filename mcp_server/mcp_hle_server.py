import asyncio
import os
import sqlite3
import textwrap
import uuid
import base64
import io
from dataclasses import dataclass
from typing import Annotated, Optional, List, Dict

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp.server.auth.provider import AccessToken
from mcp.types import INVALID_PARAMS
from mcp import ErrorData, McpError
from pydantic import BaseModel, Field
try:
    # Optional content classes for structured image responses
    from mcp.types import ImageContent, TextContent  # type: ignore
except Exception:  # pragma: no cover
    ImageContent = None  # type: ignore
    TextContent = None  # type: ignore
try:
    from PIL import Image  # type: ignore
except Exception:
    Image = None  # type: ignore

# Load env
load_dotenv()

AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER", "")  # optional

# Default DB path: ../hle_pipeline/data/hle_quiz.db relative to this file
DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../hle_pipeline/data/hle_quiz.db")
)
DB_PATH = os.environ.get("DB_PATH", DEFAULT_DB_PATH)

if not AUTH_TOKEN:
    # NOTE: For testing only. In production, set AUTH_TOKEN via .env and remove this fallback.
    print("[WARN] AUTH_TOKEN not set; using insecure test token 'dev'.")
    AUTH_TOKEN = "dev"

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

def _wrap(text: str, width: int = 76) -> str:
    return "\n".join(textwrap.wrap(text, width=width)) if text else ""


# ============ Summary tools ============

def _get_db_summary(conn: sqlite3.Connection) -> dict:
    total_questions = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]

    # Subject counts
    subject_counts_rows = conn.execute(
        """
        SELECT subject, COUNT(*) as count
        FROM questions
        GROUP BY subject
        ORDER BY count DESC
        """
    ).fetchall()
    subject_counts = {row[0]: row[1] for row in subject_counts_rows}

    # Difficulty counts
    difficulty_counts_rows = conn.execute(
        """
        SELECT difficulty, COUNT(*) as count
        FROM questions
        GROUP BY difficulty
        ORDER BY count DESC
        """
    ).fetchall()
    difficulty_counts = {row[0]: row[1] for row in difficulty_counts_rows}

    # Question type counts
    qtype_counts_rows = conn.execute(
        """
        SELECT question_type, COUNT(*) as count
        FROM questions
        GROUP BY question_type
        ORDER BY count DESC
        """
    ).fetchall()
    question_type_counts = {row[0]: row[1] for row in qtype_counts_rows}

    return {
        "total_questions": total_questions,
        "subjects": list(subject_counts.keys()),
        "difficulties": list(difficulty_counts.keys()),
        "question_types": list(question_type_counts.keys()),
        "subject_counts": subject_counts,
        "difficulty_counts": difficulty_counts,
        "question_type_counts": question_type_counts,
    }


# (Removed non-WA summary and pretty variants to keep WA-only tools)


# ============ WhatsApp-friendly tools ============

def _format_question_wa(q: Question) -> str:
    parts: List[str] = [
        "*HLE Question*",
        _wrap(q.question.strip(), 70),
        "",
    ]
    if q.subject:
        parts.append(f"- 📚 Subject: {q.subject}")
    if q.difficulty:
        parts.append(f"- 🎯 Difficulty: {q.difficulty}")
    if q.question_type:
        parts.append(f"- 🧩 Type: {q.question_type}")
    parts.append(f"- 🆔 `{q.id}`")
    return "\n".join(parts)


def _format_answer_wa(is_correct: bool, ground_truth: str, explanation: str) -> str:
    header = "*Result*"
    verdict = "✅ Correct" if is_correct else "❌ Incorrect"
    lines: List[str] = [
        header,
        verdict,
        f"🔎 Ground truth: {ground_truth}",
    ]
    if explanation:
        lines += ["", "*Explanation*", _wrap(explanation, 70)]
    return "\n".join(lines)


def _format_quiz_wa(questions: List[Question]) -> str:
    header = f"*HLE Quiz* — {len(questions)} question{'s' if len(questions) != 1 else ''}"
    lines: List[str] = [header, ""]
    for idx, q in enumerate(questions, start=1):
        lines.append(f"*{idx}.* {_wrap(q.question.strip(), 70)}")
        if q.subject:
            lines.append(f"   - 📚 Subject: {q.subject}")
        if q.difficulty:
            lines.append(f"   - 🎯 Difficulty: {q.difficulty}")
        if q.question_type:
            lines.append(f"   - 🧩 Type: {q.question_type}")
        lines.append(f"   - 🆔 `{q.id}`")
        lines.append("")
    # Remove trailing blank line
    if lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _format_single_question_wa(q: Question, idx: int, total: int) -> str:
    header = f"*Question {idx}/{total}*"
    parts: List[str] = [
        header,
        _wrap(q.question.strip(), 70),
        "",
    ]
    if q.subject:
        parts.append(f"- 📚 Subject: {q.subject}")
    if q.difficulty:
        parts.append(f"- 🎯 Difficulty: {q.difficulty}")
    if q.question_type:
        parts.append(f"- 🧩 Type: {q.question_type}")
    # Intentionally do not expose the question ID to the end user
    return "\n".join(parts)


@dataclass
class SessionState:
    questions: List[Question]
    current_index: int = 0
    correct_count: int = 0


QUIZ_SESSIONS: Dict[str, SessionState] = {}

@mcp.tool(description="WhatsApp-friendly formatted question. Use when messaging users.")
async def play_exam_wa(
    subject: Annotated[Optional[str], Field(description="Optional subject filter (e.g., Physics)")] = None,
    question_type: Annotated[Optional[str], Field(description="Optional question type filter")] = None,
) -> str:
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
        sql += " ORDER BY RANDOM() LIMIT 10"

        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        if not rows:
            cur = conn.execute(
                "SELECT id, question, subject, difficulty, question_type FROM questions ORDER BY RANDOM() LIMIT 10"
            )
            rows = cur.fetchall()
        if not rows:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="No question available (database empty)"))
        questions = [Question(**dict(r)) for r in rows]
        return _format_quiz_wa(questions)


@mcp.tool(description="Start a 10-question WhatsApp quiz (one-by-one). Random subject/type; optional difficulty_level 1-5. Returns the first question. Requires user_id.")
async def start_quiz_wa(
    user_id: Annotated[str, Field(description="Unique user id (e.g., phone number)")],
    difficulty_level: Annotated[Optional[int], Field(description="Optional difficulty 1-5: 1 easiest, 5 hardest (based on length)")] = None,
) -> str:
    with get_conn() as conn:
        sql = "SELECT id, question, subject, difficulty, question_type FROM questions WHERE 1=1"
        params: list = []
        # Map difficulty_level (1..5) to length-based bins
        try:
            lvl = int(difficulty_level) if difficulty_level is not None else None
        except Exception:
            lvl = None
        if lvl is not None and 1 <= lvl <= 5:
            if lvl == 1:
                sql += " AND LENGTH(question) < 80"
            elif lvl == 2:
                sql += " AND LENGTH(question) BETWEEN 80 AND 140"
            elif lvl == 3:
                sql += " AND LENGTH(question) BETWEEN 140 AND 220"
            elif lvl == 4:
                sql += " AND LENGTH(question) BETWEEN 220 AND 300"
            elif lvl == 5:
                sql += " AND LENGTH(question) > 300"
        sql += " ORDER BY RANDOM() LIMIT 10"

        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        if not rows:
            cur = conn.execute(
                "SELECT id, question, subject, difficulty, question_type FROM questions ORDER BY RANDOM() LIMIT 10"
            )
            rows = cur.fetchall()
        if not rows:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="No question available (database empty)"))

    questions = [Question(**dict(r)) for r in rows]
    # Start/overwrite session for this user
    QUIZ_SESSIONS[user_id] = SessionState(questions=questions)

    first = questions[0]
    return _format_single_question_wa(first, idx=1, total=len(questions))


@mcp.tool(description="WhatsApp-friendly formatted answer check.")
async def check_answer_wa(
    question_id: Annotated[str, Field(description="The question id returned by play_exam")],
    answer: Annotated[str, Field(description="User's answer text")],
) -> str:
    answer_norm = (answer or "").strip().lower()
    if not answer_norm:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Answer cannot be empty"))
    with get_conn() as conn:
        cur = conn.execute("SELECT answer, explanation FROM questions WHERE id = ?", (question_id,))
        row = cur.fetchone()
        if not row:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="Unknown question id"))
        gt = (row["answer"] or "").strip().lower()
        is_correct = (answer_norm == gt) or (gt in answer_norm) or (answer_norm in gt)
        expl = row["explanation"] or ""
        return _format_answer_wa(is_correct=is_correct, ground_truth=row["answer"], explanation=expl)


@mcp.tool(description="Submit an answer for the current question. Returns verdict and next question or final score. Requires user_id.")
async def answer_quiz_wa(
    user_id: Annotated[str, Field(description="Unique user id (e.g., phone number)")],
    answer: Annotated[str, Field(description="User's answer text")],
) -> str:
    state = QUIZ_SESSIONS.get(user_id)
    if state is None:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="No active quiz for this user. Say 'start quiz' to begin."))

    # Identify current question
    if state.current_index >= len(state.questions):
        return f"Quiz already completed. Score: {state.correct_count}/{len(state.questions)}"

    current_q = state.questions[state.current_index]
    normalized_answer = (answer or "").strip().lower()
    if not normalized_answer:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Answer cannot be empty"))

    # Look up ground truth from DB to avoid exposing in session state
    with get_conn() as conn:
        cur = conn.execute("SELECT answer FROM questions WHERE id = ?", (current_q.id,))
        row = cur.fetchone()
        if not row:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="Question not found in DB"))
        gt = (row[0] or "").strip().lower()

    is_correct = (normalized_answer == gt) or (gt in normalized_answer) or (normalized_answer in gt)
    if is_correct:
        state.correct_count += 1

    # Advance to next question
    state.current_index += 1
    remaining = len(state.questions) - state.current_index

    verdict = "✅ Right answer" if is_correct else "❌ Better luck next time"

    if remaining <= 0:
        # End of quiz: remove session
        total = len(state.questions)
        score_line = f"🎉 Quiz complete. Score: {state.correct_count}/{total}"
        # Clean up session
        QUIZ_SESSIONS.pop(user_id, None)
        return "\n".join([verdict, score_line])

    next_q = state.questions[state.current_index]
    prompt_next = _format_single_question_wa(next_q, idx=state.current_index + 1, total=len(state.questions))
    return "\n".join([verdict, "", prompt_next])


@mcp.tool(description="WhatsApp-friendly formatted database summary.")
async def db_summary_wa() -> str:
    with get_conn() as conn:
        stats = _get_db_summary(conn)

    lines: List[str] = [
        "*DB Summary*",
        f"*Total questions*: {stats['total_questions']}",
        "",
        "*By subject*",
    ]
    for subj, count in stats["subject_counts"].items():
        lines.append(f"- {subj}: {count}")
    lines += [
        "",
        "*By difficulty*",
    ]
    for diff, count in stats["difficulty_counts"].items():
        lines.append(f"- {diff}: {count}")
    lines += [
        "",
        "*By question type*",
    ]
    for qt, count in stats["question_type_counts"].items():
        lines.append(f"- {qt}: {count}")

    return "\n".join(lines)


# ============ Media tools ============

@mcp.tool(description="Convert a base64 image to black-and-white and return as image content.")
async def make_img_black_and_white(
    puch_image_data: Annotated[str, Field(description="Base64-encoded image data to convert to black and white")],
) -> list:
    if not puch_image_data:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="puch_image_data is required"))
    if Image is None:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Pillow is not installed on the server"))

    try:
        raw = base64.b64decode(puch_image_data, validate=True)
    except Exception:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Invalid base64 image data"))

    try:
        with Image.open(io.BytesIO(raw)) as img:
            bw = img.convert("L")
            buf = io.BytesIO()
            bw.save(buf, format="PNG")
            bw_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Unable to process image"))

    if ImageContent is not None:
        return [ImageContent(type="image", mimeType="image/png", data=bw_base64)]  # type: ignore
    # Fallback to dict format if ImageContent class is unavailable
    return [{"type": "image", "mimeType": "image/png", "data": bw_base64}]

async def main():
    print(f"🚀 HLE MCP on http://0.0.0.0:8086  (DB: {DB_PATH})")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())
