# PM Feedback Synthesizer: System Overview

Internal summary of what the system does and its current status, as of the Month 2 local MVP review (Week 6).

## What it does

A single API endpoint (`POST /api/feedback/analyze`) takes a piece of raw user feedback text and an optional product context string, and returns a structured breakdown: named themes with descriptions, direct quotes, sentiment, and priority, plus a summary with overall sentiment, key strengths and weaknesses, and recommended actions — all as typed JSON, ready to feed a dashboard or report without further parsing.

Each submission is also compared against previously submitted feedback stored in a vector index. If a genuinely similar prior entry exists, it's surfaced as context to the model, so recurring issues get correctly counted as recurring rather than treated as new every time.

## How it works, briefly

1. **Retrieve.** The incoming feedback is embedded and compared against a Pinecone vector index of previously submitted feedback. Matches above a similarity threshold (0.85) are pulled in as context.
2. **Ingest.** The new feedback is added to the index for future queries to match against. Long entries (over ~100 words) are split into overlapping chunks first, so a single multi-topic submission doesn't get embedded as one diluted vector.
3. **Synthesize.** The feedback, product context, and any retrieved similar entries are sent to Claude with a system prompt that extracts themes, sentiment, and priority in a fixed JSON structure.
4. **Return.** The structured result is validated and returned to the caller.

This is a **structured single-pass tool with retrieval-augmented context**, not a full multi-stage RAG pipeline — retrieval informs a single synthesis call rather than driving multi-step reasoning or reranking. A full RAG extension (Project B's broader retrieval-quality work) is a separate, still-in-progress track; this describes what's actually running in production today.

## Reliability, as verified this week

- **Structural consistency**: every response matches the expected schema exactly, across all tested inputs.
- **Priority calibration**: genuine blockers are correctly flagged critical; positive feedback and minor friction are correctly scored lower, not defaulted to a single severity.
- **Sentiment handling**: mixed feedback (a genuine positive alongside a genuine negative) is represented as `mixed` with an appropriately weighted score, not forced into a binary.
- **Recurrence tracking**: an exact repeat of prior feedback is correctly recognized and counted as a second occurrence rather than a new issue.
- **Edge cases tested**: empty/fresh index state, very long multi-topic documents, and low-signal/nonsense input have all been verified to behave sensibly (see Thursday's session notes for detail).

## Known limitations

- **Recurrence detection is similarity-based, not semantic-cluster-based.** Two reports of the same underlying bug in different words (e.g., "freezes on load" vs. "spinner never finishes") may not be recognized as the same occurrence if they fall under the 0.85 similarity threshold. Occurrence counts should be read as a lower bound on true frequency, not an exact count.
- **Newly ingested entries are not instantly retrievable.** Pinecone's indexing has a short propagation delay; a query sent immediately after a related entry is ingested may not find it yet, even though it will on a subsequent query.
- **No reranking stage.** Validated as beneficial in experimentation but deliberately deferred (see `RETRIEVAL_STRATEGY.md`) given conditional chunking already addresses most of the contamination risk it would solve.

## Status

Local MVP, verified working end to end through repeated manual testing. Not yet deployed; no automated test suite yet (all verification to date has been manual, structured testing sessions).
