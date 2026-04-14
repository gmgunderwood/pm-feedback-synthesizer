import { Router } from "express";
import { anthropic } from "@workspace/integrations-anthropic-ai";
import { AnalyzeFeedbackBody } from "@workspace/api-zod";

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

Return ONLY valid JSON. No markdown, no explanation, just the JSON object.`;

  const userMessage = productContext
    ? `Product context: ${productContext}\n\nUser feedback to analyze:\n${feedback}`
    : `User feedback to analyze:\n${feedback}`;

  try {
    const message = await anthropic.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 8192,
      messages: [
        { role: "user", content: userMessage }
      ],
      system: systemPrompt,
    });

    const block = message.content[0];
    if (block.type !== "text") {
      res.status(500).json({ error: "Unexpected response format from AI" });
      return;
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(block.text);
    } catch {
      req.log.error({ text: block.text }, "Failed to parse AI JSON response");
      res.status(500).json({ error: "AI returned malformed JSON. Please try again." });
      return;
    }

    res.json(parsed);
  } catch (err) {
    req.log.error({ err }, "Anthropic API error");
    res.status(500).json({ error: "Failed to analyze feedback. Please try again." });
  }
});

export default feedbackRouter;
