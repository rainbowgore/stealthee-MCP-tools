# Stealthee - AI-Powered Stealth Launch Detection

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Server-4b8bbe)](https://github.com/nimbleai/mcp)
[![FastMCP](https://img.shields.io/badge/FastMCP-Enabled-green)](https://github.com/nimbleai/mcp)
[![Smithery](https://img.shields.io/badge/Smithery-Compatible-%23007acc)](https://smithery.tools/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Integrated-orange)](https://platform.openai.com/)
[![Tavily](https://img.shields.io/badge/Tavily-Search-green)](https://docs.tavily.com/)
[![Nimble](https://img.shields.io/badge/Nimble-AI%20Parsing-purple)](https://docs.nimbleai.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](https://opensource.org/licenses/MIT)

Stealthee is a real-time AI system that detects stealth product launches before they trend.  
It surfaces early indicators from across the web using intelligent search, structured parsing, and OpenAI-powered scoring.

Use it if you're:

- An **investor** hunting for pre-traction signals
- A **founder** scanning for competitors before launch
- A **researcher** tracking emerging markets
- A **developer** building agents, dashboards, or alerting tools that need fresh product intel.

---

## What's cookin'?

- **Intelligent Web Search** across tech news, Product Hunt, and niche sources
- **Content Extraction** from raw URLs using AI parsers (Tavily + Nimble)
- **Stealth Scoring** using OpenAI to assess likelihood of stealth mode
- **Structured Field Parsing** (pricing tables, changelogs, CTAs, etc.)
- **Batch Tools** for high-volume analysis
- **End-to-End Pipeline** that runs search → extract → score
- **Realtime Slack Alerts** for high-confidence findings
- **Persistent SQLite Storage** for repeatable analysis and history

---

## Interfaces

You can use Stealthee through any of the following:

| Interface          | Description                                | Launch Command                                                   |
| ------------------ | ------------------------------------------ | ---------------------------------------------------------------- |
| **Claude Desktop** | Local agent UI via MCP (stdio)             | `python mcp_server_stdio.py`                                     |
| **Smithery**       | Web-based UI for tool chaining and testing | `python -m smithery.cli.playground stealth_server:create_server` |
| **Terminal/API**   | Run via Python or curl/postman             | `curl ...` or import tool functions directly                     |

---

## Installation

### Prerequisites

- **Python 3.12+**
- API Keys for: `Tavily`, `OpenAI`, (optional: `Nimble`, `Slack`)

### Quick Start

```bash
git clone https://github.com/rainbowgore/stealthee-MCP-tools
cd stealthee-MCP-tools

python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

pip install -r requirements.txt

cp .env.example .env
# 🔐 Fill in your API keys in .env
```
