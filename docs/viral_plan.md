## Viral Feature Implementation Plan

Scoped to current stack: `mcp_server` (FastMCP), `hle_pipeline` (SQLite ingest). Redis optional; Postgres later.

### Phase 0 — Baseline hardening (1–2 days)
- Database additions in `hle_pipeline/core/database_manager.py`:
  - `user_profiles(user_id, display_name, created_at)`
  - `sessions(session_id, user_id, subject, created_at, last_activity_at)`
  - `served_questions(session_id, question_id, served_at)`
- MCP server:
  - Refactor `mcp_server/mcp_hle_server.py` into modules (auth, db, tools, models).
  - `play_exam(subject?, question_type?, session_id?)` records served IDs.
- Optional Redis for rate limits and served-ID cache: `REDIS_URL`.

### Phase 1 — Adaptive testing (IRT-lite) (3–5 days)
- Schema:
  - `question_calibration(question_id, a, b, c, source, updated_at)`
  - `user_ability(user_id, subject, theta, theta_var, updated_at)`
- Offline calibration script `scripts/calibrate_items.py` (bootstrap a,b via heuristics or Rasch/2PL).
- MCP tools:
  - `start_adaptive(session_id?, subject?)` → returns first item + `session_id`.
  - `next_adaptive(session_id)` → selects item by max Fisher information (2PL), avoids repeats.
  - `submit_answer(session_id, question_id, answer, confidence?)` → updates θ.

### Phase 2 — Calibration scoring + leaderboards (2–4 days)
- Extend `user_results` with `confidence REAL, log_score REAL, brier_score REAL`.
- Compute proper scores in answer submission.
- Leaderboards (daily/weekly): `leaderboards(kind, subject?)`.

### Phase 3 — Human vs Model duel (3–5 days)
- Integrate baseline model (`MODEL_PROVIDER`, `MODEL_API_KEY`).
- Store `model_baselines(question_id, model_id, answer, is_correct, latency_ms, created_at)`.
- MCP: `duel(question_id, user_answer, confidence?)` → compare user vs model, return “You beat the model?”.

### Phase 4 — Multiplayer (head‑to‑head, group battle) (5–8 days)
- Prefer Redis for timing/state; migrate to Postgres later.
- Schema: `matches`, `match_participants`, `match_questions`.
- MCP tools: `create_match`, `join_match`, `start_match`, `submit_match_answer`, `match_state`.

### Phase 5 — Short‑answer judging with grounding (4–7 days)
- Use HLE `rationale` as rubric; store `grounding_snippets(question_id, text, source_ref)`.
- LLM judge constrained to rubric; store verdict + citations.
- Appeals: `appeals(...)` and `appeal(question_id, answer, rationale?)`.

### Phase 6 — Dynamic difficulty + spaced repetition (3–5 days)
- `sr_cards(user_id, question_id, bucket, next_review_at, last_result)` (Leitner).
- Streaks/power‑ups: `user_powerups(user_id, type, count)`.
- MCP: `sr_next(user_id, subject?)`, `sr_submit(question_id, correct)`.

### Phase 7 — Referral & virality (3–5 days; host‑dependent)
- Signed deep links; shareable result cards.
- Tournaments: `tournaments`, `tournament_scores`.
- MCP: `challenge_link(target_score, subject?)`, `tournament_info`, `tournament_submit`.

### Phase 8 — Multi‑modal, STT/TTS (3–6 days; host‑dependent)
- Return `image_url`/`image_b64` for image questions.
- Voice via host transcription; server accepts text.
- MCP: `play_exam(subject?, type=text|image)`.

### Phase 9 — Anti‑cheat & integrity (2–4 days)
- Server timers, shuffle options, retry limits.
- Canary detection in judged context.

### Phase 10 — Live analytics (2–4 days)
- Event logging → SQLite/Postgres, optional ClickHouse sink.
- Admin `stats()` summaries.

### Data model additions (summary)
- `question_calibration(...)`
- `user_ability(user_id, subject, theta, theta_var, updated_at)`
- `sessions(...)`, `served_questions(...)`
- `user_results` add: `confidence, log_score, brier_score`
- `model_baselines`, `matches`, `match_participants`, `match_questions`
- `grounding_snippets`, `appeals`, `sr_cards`, `events`

### Tech choices
- Keep SQLite + Redis early; plan Postgres for multiplayer/tournaments.
- Background jobs for calibration refresh.
- Secrets: `MODEL_PROVIDER`, `MODEL_API_KEY`, `REDIS_URL`, `DB_DSN` (when Postgres).

### Testing & rollout
- Unit tests for θ estimation and item selection.
- Simulated matches for timing/leaderboards.
- Feature flags/env toggles for gradual enablement.

### Timeline (sequential; parallelize with 2+ devs)
- Phases 0–2: ~1–2 weeks
- Phases 3–4: ~2 weeks
- Phases 5–6: ~2 weeks
- Phases 7–10: ~2–3 weeks

### Host dependencies
- Confidence slider, deep links, group orchestration, voice attachments rely on the WhatsApp host UX/runtime. We expose MCP tools/state; host implements chat flows.


