  Make it technically impressive (and viral) on WhatsApp

  • Adaptive testing (IRT)
    • Estimate user ability θ with a 2‑PL logistic model and pick next question maximizing information.
    • Show “skill map” across subjects after 10–15 questions.
  • Calibration scoring (not just accuracy)
    • Require a confidence slider (0–100%) on each answer; score with a proper scoring rule (e.g., log score/Brier).
    • Leaderboards by “well‑calibrated accuracy” to reward honesty and expertise.
  • Human vs Model duel
    • For each question, also run a baseline model (same context limits) and show “You beat the model!” or not.
    • Per‑subject “human advantage” charts; viral brag cards.
  • Multiplayer modes in WhatsApp
    • Head‑to‑head Blitz (same 5 questions, 10s each, real‑time scoring).
    • Group battle in WhatsApp groups using message buttons; anti‑cheat via randomized options and timers.
  • Short‑answer judging with grounding
    • Retrieval of the question’s rubric/excerpt; LLM judge constrained to that excerpt.
    • Store rubric hits/misses and citations; allow instant appeal -> human review queue.
  • Dynamic difficulty + spaced repetition
    • If wrong, enqueue variants of the concept; resurface later (Leitner).
    • “Streak freeze” power‑ups to keep streaks alive; boosts engagement.
  • Referral and virality loops
    • One‑tap “Challenge a friend” deep link that enters a duel with your score as target.
    • Weekly tournaments; shareable result cards (image + subject badges).
  • Multi‑modal
    • HLE includes images; support image questions in WhatsApp (media templates).
    • Voice answers: speech‑to‑text for accessibility; TTS for reading questions aloud.
  • Anti‑cheat and integrity
    • Shuffle options; strict per‑question timers; limit retries; server‑side scoring only.
    • Canary detection in user‑submitted items; disallow external content in judged context.
  • Live analytics
    • Real‑time dashboard (ClickHouse + Materialize or Supabase Realtime): DAU, retention, conversion, virality K‑factor, question
      difficulty curve.