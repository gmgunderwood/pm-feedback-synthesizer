# PM Feedback Synthesizer

## What it does

Takes raw user feedback text and returns a structured breakdown: named themes with descriptions, sentiment, priority, and direct quotes, plus a summary with overall sentiment, key strengths and weaknesses, and recommended actions. Each submission is also compared against previously submitted feedback, so recurring issues get correctly counted as recurring rather than treated as new every time.

## Live demo

**[pm-feedback-synthesizer.replit.app](https://pm-feedback-synthesizer.replit.app)**

Example outputs from stability and stress testing (20 diverse queries, zero crashes or guard failures):

**Positive feedback handling**

![Positive feedback example 1](screenshots/positive1.png)
![Positive feedback example 2](screenshots/positive2.png)
![Positive feedback example 3](screenshots/positive3.png)

**Negative feedback handling**

![Negative feedback example 1](screenshots/negative1.png)
![Negative feedback example 2](screenshots/negative2.png)
![Negative feedback example 3](screenshots/negative3.png)

**Prompt injection resistance** — the tool correctly refuses to comply with embedded instructions and instead classifies the input as a security-testing attempt:

![Prompt injection resistance example 1](screenshots/prompt1.png)
![Prompt injection resistance example 2](screenshots/prompt2.png)

## Architecture

This is a **structured single-pass tool with retrieval-augmented context**, not a full multi-stage RAG pipeline. Retrieval informs a single synthesis call rather than driving multi-step reasoning, reranking, or agentic tool use. A full RAG extension is a separate, in-progress track; this README describes what's actually running today.

**Flow per request:**
1. **Retrieve.** The incoming feedback is embedded and compared against a Pinecone vector index of previously submitted feedback. Matches above a similarity threshold are pulled in as context.
2. **Ingest.** The new feedback is added to the index for future requests to match against. Retrieval always runs before ingestion within the same request, so a request can never match against itself.
3. **Synthesize.** The feedback, optional product context, and any retrieved similar entries are sent to Claude with a system prompt that extracts themes, sentiment, and priority in a fixed JSON structure.
4. **Return.** The structured result is validated and returned to the caller.

## How retrieval works

- **Embedding model:** Pinecone's hosted `multilingual-e5-large`, via integrated inference. Embedding happens automatically as part of the ingestion upsert call — there's no separate embeddings API call anywhere in this codebase.
- **Similarity metric:** cosine similarity, comparing the angle between vectors rather than raw distance, so retrieval isn't skewed by how long a piece of feedback happens to be.
- **Threshold:** only matches scoring above **0.85** are treated as relevant context, tuned empirically after a documented false positive at a looser 0.807 threshold.
- **Chunking:** entries over ~100 words are split into overlapping 50-word chunks before ingestion, so a single long, multi-topic entry doesn't get embedded as one diluted vector.
- **Dense retrieval only, no lexical/hybrid component.** This is a deliberate choice: the goal is catching the same complaint worded differently, which is exactly where a keyword-matching approach (like BM25) would fall short. A hybrid approach would be worth adding if testing showed the system specifically missing exact-term queries (names, codes, acronyms) — not as a preemptive addition.
- **Retrieved context is explicitly scoped in the prompt.** Retrieved past entries are labeled as background only, used to detect recurring issues and increment occurrence counts — never blended into the current submission's executive summary, strengths, weaknesses, or quotes unless the current submission independently says the same thing. This was tightened after stress testing surfaced a case where a retrieved entry's specifics leaked into an unrelated submission's summary (see Reliability section below).

## Technical choices

| Decision | Rationale |
|---|---|
| Pinecone integrated embedding over a separate embeddings API | No separate embeddings pipeline or provider API key to manage; embedding happens as a side effect of the upsert call |
| Dense/semantic retrieval only, no BM25 or hybrid | Prioritizes catching paraphrased recurring complaints over exact keyword matches |
| 0.85 similarity threshold | Empirically tuned after a documented false positive at 0.807 |
| Conditional chunking (only entries >100 words) | Prevents long, multi-topic entries from diluting retrieval quality without adding chunking overhead to short entries |
| Retrieval before ingestion, always | Guarantees a request can never retrieve its own just-ingested text |
| Explicit scoping instructions for retrieved context in the system prompt | Prevents retrieved-context specifics from bleeding into the current submission's summary, strengths, weaknesses, or quotes |

## Reliability

20 diverse queries were run against the deployed instance to stress-test edge cases beyond normal happy-path feedback: extremely short and long submissions, non-English input, sarcasm, prompt injection attempts, spam/URL content, empty/whitespace-only submissions, ALL CAPS with profanity, technical stack traces, bundled unrelated complaints, and exact and near-exact repeats to verify occurrence tracking.

**Result: zero crashes, zero guard failures, zero rate-limit trips across all 20 queries.** Notable strengths surfaced by the stress test:
- Correctly classifies sarcastic feedback as negative despite surface-level positive wording
- Refuses to comply with embedded prompt injection instructions and instead flags the input as a security-testing attempt
- Correctly identifies and flags spam/promotional content rather than fabricating themes from it
- Handles non-English input (tested in Portuguese) with fluent, accurate English output
- Priority calibration reflects severity and workflow impact, not just text length or word count

One real bug was found and fixed during this testing: retrieved past-feedback context was occasionally blended into the current submission's executive summary without attribution. See "How retrieval works" above for the fix.

## Known limitations

- **Recurrence detection is similarity-threshold-based, not semantic-cluster-based.** Two descriptions of the same underlying issue in sufficiently different words may not be recognized as a repeat. Occurrence counts should be read as a lower bound on true frequency, not an exact count.
- **Pinecone indexing has a real propagation delay.** A query sent immediately after a related entry is ingested may legitimately retrieve nothing, even though the entry is genuinely in the index moments later.
- **Theme grouping is not perfectly stable across runs.** The same underlying recurring issue can occasionally be split into a different number of themes with different names depending on the current submission's exact wording, even though occurrence counts for the underlying issue remain accurate.
- **The 10,000-character length guard's exact boundary behavior is untested.** The guard is implemented and rejects overlong submissions, but stress testing did not include a submission landing precisely at the boundary, so its exact behavior there (clean rejection vs. edge-case handling) has not been directly verified.

## How to run it locally

**Prerequisites:** Node.js, pnpm, an Anthropic API key, a Pinecone API key.

```bash
git clone https://github.com/gmgunderwood/pm-feedback-synthesizer.git
cd pm-feedback-synthesizer
pnpm install
```

Create `artifacts/api-server/.env` with:
ANTHROPIC_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
PORT=3000
Start the server:

```bash
pnpm --filter api-server dev
```

Test it:

```bash
curl -X POST http://localhost:3000/api/feedback/analyze \
  -H "Content-Type: application/json" \
  -d '{"feedback": "The export button is broken and crashes every time.", "productContext": "B2B analytics dashboard"}'
```
