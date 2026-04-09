# 🔬 AI Research Digest Agent

[![Daily AI Research Digest](https://github.com/RahulNarayananan/AI-Research_digest/actions/workflows/daily_digest.yml/badge.svg)](https://github.com/RahulNarayananan/AI-Research_digest/actions/workflows/daily_digest.yml)

An autonomous AI agent that fetches, ranks, and summarizes the top trending research papers to deliver a curated daily digest directly to your inbox.

## ✨ Features
- **Multi-Source Discovery**: Aggregates trending papers from **Hugging Face** (Industry Buzz) and **Papers With Code** (GitHub Traction).
- **Smart Ranking**: Prioritizes papers with high social discussion, academic influence, and real-world code implementations.
- **AI-Driven Summaries**: Uses **Google Gemini 1.5 Flash** to provide concise, 1-2 sentence insights on why each paper matters.
- **Clean UI**: Beautiful dark-mode HTML email layout with source badges and clear technical breakdowns.
- **Autonomous Execution**: Runs daily at 00:00 UTC (08:00 SGT) via GitHub Actions.

## 🛠️ Setup
1. Clone the repository.
2. Create a `.env` file from `.env.example`.
3. Fill in your `GEMINI_API_KEY`, `SENDER_EMAIL`, and `SENDER_APP_PASSWORD`.
4. Configure GitHub Repository Secrets for automated runs.

---
*Created with ❤️ by Antigravity*
