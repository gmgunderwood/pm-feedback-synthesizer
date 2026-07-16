# Retrieval Strategy: Decisions and Rationale

This document records the final decisions made on Project B's retrieval quality
after two weeks of experimentation (chunking strategy, reranking), and the
evidence behind them. Intended to be linked from or folded into the main
README once finalized.

## Summary

| Decision | Status |
|---|---|
| Conditional chunking (split entries >100 words) | **Adopted** |
| Reranking as a permanent retrieval stage | **Deferred** — validated, not implemented |

---

## Decision 1: Conditional Chunking

**Adopted.** Feedback entries longer than ~100 words will be split into
50-word chunks with 10-word overlap before ingestion. Entries at or under
100 words continue to be ingested as a single whole chunk, unchanged from
the original Week 4 design.

### Why

A chunking experiment (Week 5, Wednesday) tested two strategies — 50-word
chunks (10-word overlap) vs. 150-word chunks (20-word overlap) — against the
same 5 long, real, multi-topic reviews and the same 3 test queries, with each
strategy isolated in its own Pinecone namespace.

Results across all three test queries:

- Small chunks won or tied every comparison, and never introduced an
  unrelated document into the results.
- Large chunks introduced cross-document contamination twice: an unrelated
  flight-booking app appeared in a golf GPS query, and dark-mode content from
  an unrelated review intruded on a pricing query.

The mechanism: a chunk that spans multiple topics gets compressed into a
single averaged embedding. A query resembling any fragment of that mix can
pull the whole chunk in, irrelevant portions included. Smaller chunks split
reviews at more natural topic boundaries, so this is far less likely.

### Why *conditional*, not universal, chunking

Most entries in the actual feedback dataset are short — a single sentence or
two. Chunking a short entry does nothing (it can't meaningfully be split) and
only adds ingestion overhead and extra Pinecone records with no retrieval
benefit. The problem chunking solves is specific to long, multi-topic text,
so the fix is scoped to where the evidence actually showed a problem, rather
than applied uniformly.

### Implementation notes (for when this is built)

- Threshold: entries over ~100 words get chunked; at/under, unchanged.
- Chunk parameters: 50 words per chunk, 10-word overlap (the tested,
  evidence-backed values — not arbitrary defaults).
- The `chunk_utils.py` sliding-window function built for the experiment
  (`project-a/chunk_utils.py`) is directly reusable for this; it was tested
  against both short and long text and handles the sub-threshold case
  (returns the text unchanged) automatically.

---

## Decision 2: Reranking — Validated, Deferred

**Not implemented as a permanent stage right now.** The technique is proven
effective and the implementation path is understood, but it isn't being added
to the production retrieval pipeline at this time.

### Why it works

A reranking experiment (Week 5, Thursday) added a cross-encoder reranking
step on top of initial vector retrieval, tested with/without across the same
queries and namespaces as the chunking experiment.

Reranking does not shrink a fixed-size result list — asking for the top 3
still returns 3 results even if only 1–2 are genuinely relevant. What it
changes is the *score* attached to each result, and that turned out to matter
a great deal. In the GPS-accuracy query against large chunks, the
contaminating result (an unrelated flight-booking app) had a raw similarity
score of 0.762 — close enough to the genuine matches (0.768–0.815) that no
reasonable similarity threshold could cleanly separate them. After reranking,
that same result's score collapsed to 0.000, while genuine matches scored
0.4–0.97. The separation between relevant and irrelevant became dramatically
clearer.

### Why deferred anyway

- **The problem it solves most clearly is now substantially smaller.**
  Conditional chunking (Decision 1) already prevents most of the
  cross-document contamination reranking was tested against. The two
  problems overlap significantly.
- **Cost.** Reranking adds an extra API call and real latency to every
  retrieval, a meaningful tradeoff for a problem that's now mostly addressed
  by chunking alone.
- **No evidence of need in production.** The month's live testing (5 diverse
  queries against the real feedback namespace, post-threshold-fix) showed
  zero false positives. Reranking was validated against a deliberately
  adversarial test case built to expose the contamination problem, not
  against evidence that the production pipeline currently has one.

### Re-visit criteria

Revisit implementing reranking as a permanent stage if:

1. Real user feedback in production starts showing retrieval contamination
   similar to what the experiment reproduced (an unrelated theme appearing in
   synthesis results), despite conditional chunking being in place, or
2. Retrieval needs to scale to a much larger and more topically diverse
   corpus, where similarity-score separation between genuine and irrelevant
   matches is less reliable than it's been so far.

If implemented, the tested approach (retrieve top 10 via vector similarity,
rerank down to top 3 using Pinecone's `bge-reranker-v2-m3` model) is the
validated starting point — see `project-a/rerank_experiment.py` for the
working reference implementation.

---

## Related Files

- `project-a/chunk_utils.py` — sliding-window chunking function
- `project-a/ingest_chunk_experiment.py` — chunking experiment ingestion script
- `project-a/query_chunk_experiment.py` — chunking experiment comparison script
- `project-a/rerank_experiment.py` — reranking experiment script
