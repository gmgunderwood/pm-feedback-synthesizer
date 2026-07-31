import { Router } from "express";
import Anthropic, { APIError } from "@anthropic-ai/sdk";
import { Pinecone } from "@pinecone-database/pinecone";
import { AnalyzeFeedbackBody } from "@workspace/api-zod";

function getAnthropicErrorMessage(err: unknown): string {
  if (err instanceof APIError) {
    if (err.status === 401) {
      return "AI service authentication failed. Please check the API key configuration.";
    }
    if (err.status === 429) {
      return "The AI service is rate-limited. Please wait a moment and try again.";
    }
    if (err.status === 529) {
      return "The AI service is temporarily overloaded. Please try again in a few minutes.";
    }
    if (err.status && err.status >= 500) {
      return "The AI service is temporarily unavailable. Please try again later.";
    }
    if (err.message) {
      return err.message;
    }
  }

  if (err instanceof Error) {
    if (err.message.includes("fetch failed") || err.message.includes("ECONNREFUSED")) {
      return "Could not reach the AI service. Please check your network connection and try again.";
    }
    return err.message;
  }

  return "Failed to analyze feedback. Please try again.";
}

if (!process.env.ANTHROPIC_API_KEY) {
  throw new Error("ANTHROPIC_API_KEY must be set.");
}

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const CHUNK_WORD_THRESHOLD = 100;
const CHUNK_SIZE_WORDS = 50;
const CHUNK_OVERLAP_WORDS = 10;

/**
 * Conditional chunking, per the Week 5 retrieval strategy decision
 * (RETRIEVAL_STRATEGY.md): entries over ~100 words get split into
 * overlapping 50-word chunks; shorter entries stay as a single whole
 * chunk, unchanged from before. This prevents a long, multi-topic entry
 * from being embedded as one diluted vector that matches poorly against
 * any single-topic future query.
 */
function chunkFeedback(text: string): string[] {
  const words = text.trim().split(/\s+/);
  if (words.length <= CHUNK_WORD_THRESHOLD) {
    return [text];
  }

  const chunks: string[] = [];
  const step = CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS;
  for (let start = 0; start < words.length; start += step) {
    const chunkWords = words.slice(start, start + CHUNK_SIZE_WORDS);
    chunks.push(chunkWords.join(" "));
    if (start + CHUNK_SIZE_WORDS >= words.length) break;
  }
  return chunks;
}

const feedbackRouter = Router();

feedbackRouter.post("/feedback/analyze", async (req, res) => {
  const parseResult = AnalyzeFeedbackBody.safeParse(req.body);
  if (!parseResult.success) {
    res.status(400).json({ error: "Invalid request body: feedback is required" });
    return;
  }

  const { feedback, productContext } = parseResult.data;

  if (!feedback || feedback.trim().length === 0) {
    res.status(400).json({ error: "Feedback text cannot be empty" });
    return;
  }

  if (feedback.length > 10000) {
    res.status(400).json({ error: "Feedback text is too long (max 10,000 characters)." });
    return;
  }

  let similarEntries: string[] = [];
  try {
    if (!process.env.PINECONE_API_KEY) {
      req.log.error("PINECONE_API_KEY is not set; skipping Pinecone retrieval");
    } else {
      const pc = new Pinecone({ apiKey: process.env.PINECONE_API_KEY });
      const index = pc.index("pm-feedback-test").namespace("feedback");
      const results = await index.searchRecords({
        query: { inputs: { text: feedback }, topK: 3 },
        fields: ["chunk_text"],
      });
      similarEntries = results.result.hits
        .filter((hit) => hit._score > 0.85)
        .map((hit) => (hit.fields as { chunk_text?: string }).chunk_text)
        .filter((text): text is string => typeof text === "string");
    }
  } catch (err) {
    req.log.error({ err }, "Pinecone retrieval failed");
    similarEntries = [];
  }

  try {
    if (!process.env.PINECONE_API_KEY) {
      req.log.error("PINECONE_API_KEY is not set; skipping Pinecone ingestion");
    } else {
      const pc = new Pinecone({ apiKey: process.env.PINECONE_API_KEY });
      const index = pc.index("pm-feedback-test").namespace("feedback");
      const chunks = chunkFeedback(feedback);
      const baseId = Date.now().toString();
      await index.upsertRecords({
        records: chunks.map((chunkText, i) => ({
          _id: chunks.length > 1 ? `${baseId}_${i}` : baseId,
          chunk_text: chunkText,
        })),
      });
      if (chunks.length > 1) {
        req.log.info({ chunkCount: chunks.length }, "Feedback split into chunks before ingestion");
      }
    }
  } catch (err) {
    req.log.error({ err }, "Pinecone ingestion failed");
  }


  const systemPrompt = `You are a senior product manager analyzing user feedback. Your job is to extract structured insights from raw user feedback text.

Analyze the provided feedback and return a JSON response with the following exact structure:
{
  "themes": [
    {
      "name": "Theme name (2-5 words)",
      "description": "Detailed description of this theme",
      "occurrences": <number of times this theme appears>,
      "quotes": ["direct quote from feedback", "another quote"],
      "sentiment": "positive" | "negative" | "neutral" | "mixed",
      "priority": "critical" | "high" | "medium" | "low"
    }
  ],
  "summary": {
    "overallSentiment": "positive" | "negative" | "neutral" | "mixed",
    "sentimentScore": <float from -1.0 to 1.0>,
    "totalThemes": <number>,
    "criticalIssues": <count of critical priority themes>,
    "keyStrengths": ["strength 1", "strength 2"],
    "keyWeaknesses": ["weakness 1", "weakness 2"],
    "recommendedActions": ["action 1", "action 2", "action 3"],
    "executiveSummary": "2-3 sentence executive summary of the feedback"
  }
}

Priority guidelines:
- critical: Bugs, blockers, data loss, security issues, things that prevent core use
- high: Major UX friction, missing key features, frequent pain points
- medium: Nice-to-have improvements, minor usability issues
- low: Cosmetic issues, edge cases, minor requests

Scoping rule for retrieved past feedback: if the user message includes a "RETRIEVED PAST FEEDBACK" section, treat it strictly as background for recognizing recurring patterns (e.g., increasing a theme's "occurrences" count when the same issue was reported before). Do NOT pull details, specifics, or quotes from retrieved past feedback into "executiveSummary", "keyStrengths", "keyWeaknesses", or "quotes" unless the CURRENT submission also states them. The "executiveSummary" and "quotes" fields must describe only what is in the current submission, in the current submission's own words. If a theme's occurrence count is being incremented because of a match found in past feedback, note that explicitly in the theme's "description" (e.g., "also reported in a prior submission") rather than presenting the past feedback's specifics as if the current user said them.

Return ONLY valid JSON. No markdown, no explanation, just the JSON object.`;

  const baseUserMessage = productContext
    ? `Product context: ${productContext}\n\nUser feedback to analyze:\n${feedback}`
    : `User feedback to analyze:\n${feedback}`;

    const userMessage =
    similarEntries.length > 0
      ? `${baseUserMessage}\n\nRETRIEVED PAST FEEDBACK (context only — this was submitted separately in the past, NOT part of the current session above) — ${similarEntries.length} ${similarEntries.length === 1 ? "entry" : "entries"}:\n${similarEntries
          .map((entry, i) => `[${i + 1}] ${entry}`)
          .join("\n")}\n\nUse this only to detect recurring issues and adjust occurrence counts. Never copy specifics from it into the executive summary, key strengths, key weaknesses, or quotes fields unless the current submission independently states the same thing.`
      : baseUserMessage;

  try {
    const message = await anthropic.messages.create({
      model: "claude-sonnet-4-5",
      max_tokens: 8192,
      messages: [{ role: "user", content: userMessage }],
      system: systemPrompt,
    });

    const block = message.content[0];
    if (!block || block.type !== "text") {
      res.status(500).json({ error: "Unexpected response format from AI" });
      return;
    }

    let parsed: unknown;
    try {
      const raw = block.text.trim();
      const stripped = raw
        .replace(/^```(?:json)?\s*/i, "")
        .replace(/\s*```\s*$/, "")
        .trim();
      parsed = JSON.parse(stripped);
    } catch {
      req.log.error({ text: block.text }, "Failed to parse AI JSON response");
      res.status(500).json({ error: "AI returned malformed JSON. Please try again." });
      return;
    }

    res.json(parsed);
  } catch (err) {
    req.log.error({ err }, "Anthropic API error");
    res.status(500).json({ error: getAnthropicErrorMessage(err) });
  }
});

export default feedbackRouter;
