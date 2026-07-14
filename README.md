# PM Feedback Synthesizer
An AI-powered tool that analyzes raw user feedback and extracts structured insights for product managers.
## What it does
Paste any user feedback — App Store reviews, support tickets, NPS comments, or interview notes — and get back:
- Executive Summary with overall sentiment score
- Feedback Themes with priority levels (Critical/High/Medium/Low)
- Key Insights including strengths, weaknesses, and recommended actions
## Retrieval-augmented analysis
Every submitted feedback entry is embedded and stored in Pinecone. Before analyzing new feedback, the app retrieves the 3 most similar past entries (similarity score > 0.85) and includes them as context, so recurring patterns get identified across submissions rather than analyzed in isolation.
## Built with
- Claude API (Anthropic)
- Pinecone (vector database, integrated embeddings via multilingual-e5-large)
- Node.js/Express backend
- Vanilla HTML/CSS/JS frontend
- Deployed on Replit
## Live demo
https://feedback-synthesizer--gmgunderwood.replit.app
