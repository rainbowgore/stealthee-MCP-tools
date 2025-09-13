# Stealthee MCP - Tools for being early

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-Server-4b8bbe)](https://github.com/nimbleai/mcp)
[![OpenAI API](https://img.shields.io/badge/OpenAI-Integrated-orange)](https://platform.openai.com/)
[![Tavily](https://img.shields.io/badge/Tavily-Search-green)](https://docs.tavily.com/)
[![Nimble](https://img.shields.io/badge/Nimble-AI%20Parsing-purple)](https://docs.nimbleai.dev/)
[![Slack Alerts](https://img.shields.io/badge/Slack-Alerts%20Enabled-4A154B?logo=slack)](https://slack.com/)
[![Smithery](https://img.shields.io/badge/Smithery-Compatible-%23007acc)](https://smithery.tools/)

![Stealthee Logo](./mcp-stealthee.png)

Stealthee is a dev-first system for surfacing pre-public product signals - before they trend.
It combines search, extraction, scoring, and alerting into a plug-and-play pipeline you can integrate into Claude, LangGraph, Smithery, or your own AI stack via MCP.

Use it if you're:

- An **investor** hunting for pre-traction signals
- A **founder** scanning for competitors before launch
- A **researcher** tracking emerging markets
- A **developer** building agents, dashboards, or alerting tools that need fresh product intel.

## What's cookin'?

### MCP Tools

| Tool                  | Description                                  |
| --------------------- | -------------------------------------------- |
| `web_search`          | Search the web for stealth launches (Tavily) |
| `url_extract`         | Extract content from URLs (BeautifulSoup)    |
| `score_signal`        | AI-powered signal scoring (OpenAI)           |
| `batch_score_signals` | Batch process multiple signals               |
| `search_tech_sites`   | Search tech news sites only                  |
| `parse_fields`        | Extract structured fields from HTML          |
| `run_pipeline`        | End-to-end detection pipeline                |

## Installation & Setup

### Prerequisites

- API keys for external services (see Environment Variables)

### Quick Start

1. **Clone and Setup**

   ```bash
   git clone https://github.com/rainbowgore/stealthee-MCP-tools
   cd stealthee-MCP-tools
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**

   Fill the `.env` file with your API keys:

   ```bash
   # Required
   TAVILY_API_KEY=your_tavily_key_here
   OPENAI_API_KEY=your_openai_key_here
   NIMBLE_API_KEY=your_nimble_key_here

   # Optional
   SLACK_WEBHOOK_URL=your_slack_webhook_here
   ```

3. **Start Servers**

   ```bash
   # MCP Server (for Claude Desktop)
   python mcp_server_stdio.py

   # FastMCP Server (for Smithery)
   smithery dev

   # FastAPI Server (Optional - Legacy)
   python start_fastapi.py
   ```

## Smithery & Claude Desktop Integration

All MCP tools listed above are available out-of-the-box in [Smithery](https://smithery.ai/server/@rainbowgore/stealthee-mcp-tools/). Smithery is a visual agent and workflow builder for AI tools, letting you chain, test, and orchestrate these tools with no code.

### Available Tools

- **web_search**: Search the web for stealth launches using Tavily.
- **url_extract**: Extract and clean content from any URL.
- **score_signal**: Use OpenAI to score a single signal for stealthiness.
- **batch_score_signals**: Score multiple signals in one go.
- **search_tech_sites**: Search only trusted tech news sources.
- **parse_fields**: Extract structured fields (like pricing, changelog) from HTML.
- **run_pipeline**: End-to-end pipeline: search, extract, parse, score, and store.

### How to Use in Smithery

1. **Open the [Stealthee MCP Tools page on Smithery](https://smithery.ai/server/@rainbowgore/stealthee-mcp-tools/).**
2. Click "Try in Playground" to test any tool interactively.
3. Use the visual workflow builder to chain tools together (e.g., search → extract → score).
4. Integrate with Claude Desktop or your own agents by copying the workflow or using the API endpoints provided by Smithery.

### Claude Desktop Integration

Add to your Claude Desktop `config.json` file:

```json
{
  "mcpServers": {
    "stealth-mcp": {
      "command": "/path/to/stealthee-MCP-tools/.venv/bin/python",
      "args": ["/path/to/stealthee-MCP-tools/mcp_server_stdio.py"],
      "cwd": "/path/to/stealthee-MCP-tools",
      "env": {
        "TAVILY_API_KEY": "your_tavily_key",
        "OPENAI_API_KEY": "your_openai_key"
      }
    }
  }
}
```
## Tool Use Cases

**For Analysts & Builders:**

- `web_search`: Find stealth product mentions across the web
- `url_extract`: Pull and clean raw text from landing pages
- `score_signal`: Judge how likely a change log implies launch
- `batch_score_signals`: Quickly triage dozens of scraped URLs
- `search_tech_sites`: Limit queries to trusted domains only
- `parse_fields`: Extract pricing/release info from messy HTML
- `run_pipeline`: Full pipeline — search → extract → parse → score


## 🔬 Signal Intelligence Workflow

1. **Search Phase**: Use `web_search` or `search_tech_sites` to find relevant URLs
2. **Extraction Phase**: Use `url_extract` to get clean content from URLs
3. **Parsing Phase**: Use `parse_fields` to extract structured data (pricing, changelog, etc.)
4. **Analysis Phase**: Use `score_signal` or `batch_score_signals` for AI-powered analysis
5. **Storage Phase**: All signals are stored in SQLite database
6. **Alert Phase**: High-confidence signals trigger Slack notifications

## ⚙️ FastAPI Server

You can also run this project as a FastAPI server for REST-style access to all MCP tools.

### Base Endpoints

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Tool Manifest**: [http://localhost:8000/tools](http://localhost:8000/tools)

---

### Example Usage

**Search for stealth launches:**

```bash
curl -X POST "http://localhost:8000/tools/web_search" \
  -H "Content-Type: application/json" \
  -d '{"query": "stealth startup AI", "num_results": 5}'
```

**Run full detection pipeline:**

```bash
curl -X POST "http://localhost:8000/tools/run_pipeline" \
  -H "Content-Type: application/json" \
  -d '{"query": "new AI product launch", "num_results": 3}'
```

### Pipeline Parameters

- `query` (required): Search phrase (e.g. "AI roadmap")
- `num_results` (optional, default: 5): Number of search results to analyze
- `target_fields` (optional, default: ["pricing", "changelog"]): Fields to extract from HTML

---

### What run_pipeline Does

1. Searches tech and stealth-friendly sources using Tavily
2. Extracts raw content from each result
3. Parses structured signals (pricing, changelog, etc.)
4. Scores each result with OpenAI to estimate stealthiness
5. Stores results in local SQLite
6. Notifies via Slack if confidence is high

### AI Scoring Logic

The score_signal and batch_score_signals tools use GPT-3.5 to evaluate:

- Stealth indicators (e.g. private changelogs, missing press, beta flags)
- Confidence level (Low / Medium / High)
- Textual reasoning (used in UI or alerting)

### Database Schema (data/signals.db)

| Field          | Type    | Description                     |
| -------------- | ------- | ------------------------------- |
| `id`           | INTEGER | Primary key                     |
| `url`          | TEXT    | Source URL                      |
| `title`        | TEXT    | Signal title                    |
| `html_excerpt` | TEXT    | First 500 characters of content |
| `changelog`    | TEXT    | Parsed changelog (optional)     |
| `pricing`      | TEXT    | Parsed pricing info (optional)  |
| `score`        | REAL    | Stealth likelihood (0–1)        |
| `confidence`   | TEXT    | Confidence level                |
| `reasoning`    | TEXT    | AI rationale for the score      |
| `created_at`   | TEXT    | ISO timestamp                   |

### Dev Quickstart (FastAPI)

```bash
python start_fastapi.py
```

Then visit: [http://localhost:8000/docs](http://localhost:8000/docs)

---

Built with 💜 for those who spot what others miss.
