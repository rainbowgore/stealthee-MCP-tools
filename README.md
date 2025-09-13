# Stealthee MCP - Tools for being early

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-Server-4b8bbe)](https://github.com/nimbleai/mcp)
[![OpenAI API](https://img.shields.io/badge/OpenAI-Integrated-orange)](https://platform.openai.com/)
[![Tavily](https://img.shields.io/badge/Tavily-Search-green)](https://docs.tavily.com/)
[![Nimble](https://img.shields.io/badge/Nimble-AI%20Parsing-purple)](https://docs.nimbleai.dev/)
[![Slack Alerts](https://img.shields.io/badge/Slack-Alerts%20Enabled-4A154B?logo=slack)](https://slack.com/)
[![Smithery](https://img.shields.io/badge/Smithery-Compatible-%23007acc)](https://smithery.tools/)

Stealthee is a dev-first system for surfacing pre-public product signals - before they trend.
It combines search, extraction, scoring, and alerting into a plug-and-play pipeline you can integrate into Claude, LangGraph, Smithery, or your own AI stack via MCP.

Use it if you're:

- An **investor** hunting for pre-traction signals
- A **founder** scanning for competitors before launch
- A **researcher** tracking emerging markets
- A **developer** building agents, dashboards, or alerting tools that need fresh product intel.

## What's cookin'?

### Core Capabilities

- **Web Search**: Search across the entire web using Tavily API
- **Content Extraction**: Extract clean text from URLs using BeautifulSoup
- **AI Scoring**: AI-powered analysis of signals for stealth launch likelihood
- **Batch Processing**: Process multiple signals efficiently in parallel
- **Tech-Focused Search**: Targeted search across tech news sites and Product Hunt
- **Field Parsing**: Extract structured data like pricing and changelog from HTML
- **End-to-End Pipeline**: Complete stealth launch detection workflow
- **Real-time Alerts**: Slack notifications for high-confidence signals
- **Database Storage**: SQLite storage for all detected signals

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

## Installation

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

3. **Start MCP Server** (for Claude Desktop)

   ```bash
   python mcp_server_stdio.py
   ```

4. **Start FastMCP Server** (for Smithery)

   ```bash
   # Test locally with Smithery playground
   python -m smithery.cli.playground stealth_server:create_server

   # Or use the dev server
   smithery dev
   ```

5. **Start FastAPI Server** (Optional - Legacy)
   ```bash
   python start_fastapi.py
   ```

## 🔧 Configuration

### Claude Desktop Integration

Add to your `claude_desktop_config.json`:

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

## 📖 Usage

### MCP Server (Claude Desktop)

The MCP server provides 7 tools that can be used directly in Claude Desktop:

1. **Search for stealth launches**:

   ```
   Use web_search to find recent stealth product launches
   ```

2. **Extract and analyze content**:

   ```
   Use url_extract to get content from a URL, then score_signal to analyze it
   ```

3. **Run complete pipeline**:
   ```
   Use run_pipeline to search, extract, parse, and score signals automatically
   ```

### FastAPI Server

Access the API at `http://localhost:8000`:

- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Tools List**: `http://localhost:8000/tools`

#### Example API Usage

```bash
# Search for stealth launches
curl -X POST "http://localhost:8000/tools/web_search" \
  -H "Content-Type: application/json" \
  -d '{"query": "stealth startup AI", "num_results": 5}'

# Run complete pipeline
curl -X POST "http://localhost:8000/tools/run_pipeline" \
  -H "Content-Type: application/json" \
  -d '{"query": "new AI product launch", "num_results": 3}'
```

### Smithery Playground

Test your tools interactively with the Smithery playground:

```bash
# Start interactive playground
python -m smithery.cli.playground stealth_server:create_server

# Or use the dev server
smithery dev
```

The playground provides:

- Interactive tool testing
- Real-time API key configuration
- Visual tool interface
- Debug logging

## Smithery Integration

This project is **natively compatible with [Smithery](https://smithery.tools/)** — a local dev UI and workflow runner for MCP tools (Model Context Protocol). If you're building AI pipelines with Claude, LangGraph, or agentic tools, Smithery gives you:

- Live GUI to test all 7 tools via interactive interface
- Auto-generated forms from tool schemas
- Support for Claude Desktop and LangGraph workflows
- Local tool orchestration + debug view

### 🔁 To use in Smithery:

```bash
# Start Smithery development server (in this repo)
smithery dev

# Or use the playground for interactive testing
python -m smithery.cli.playground stealth_server:create_server

Then open: http://localhost:3000/dev

You'll see all 7 tools from this repo available as interactive cards inside the GUI.

Tool registration is defined in src/stealthee_mcp/server.py using FastMCP decorators.
```

## 🔬 Signal Intelligence Workflow

1. **Search Phase**: Use `web_search` or `search_tech_sites` to find relevant URLs
2. **Extraction Phase**: Use `url_extract` to get clean content from URLs
3. **Parsing Phase**: Use `parse_fields` to extract structured data (pricing, changelog, etc.)
4. **Analysis Phase**: Use `score_signal` or `batch_score_signals` for AI-powered analysis
5. **Storage Phase**: All signals are stored in SQLite database
6. **Alert Phase**: High-confidence signals trigger Slack notifications

### AI Scoring

The system uses OpenAI's API to score signals based on:

- Stealth launch indicators (keywords, timing, context)
- Confidence level (Low/Medium/High)
- Detailed reasoning for the score

## Database Schema

Signals are stored in `data/signals.db` with the following schema:

| Field          | Type    | Description                     |
| -------------- | ------- | ------------------------------- |
| `id`           | INTEGER | Primary key                     |
| `url`          | TEXT    | Source URL                      |
| `title`        | TEXT    | Signal title                    |
| `html_excerpt` | TEXT    | First 500 characters of content |
| `changelog`    | TEXT    | Parsed changelog information    |
| `pricing`      | TEXT    | Parsed pricing information      |
| `score`        | REAL    | AI confidence score (0-1)       |
| `confidence`   | TEXT    | Confidence level                |
| `reasoning`    | TEXT    | AI reasoning for the score      |
| `created_at`   | TEXT    | ISO timestamp                   |

## 📁 Project Structure

```
stealthee-MCP-tools/
├── mcp_server_stdio.py          # MCP server (stdio) - for Claude Desktop
├── stealth_server.py            # FastMCP server - for Smithery deployment
├── fastapi_server.py            # FastAPI server (legacy)
├── start_fastapi.py             # FastAPI startup script
├── pyproject.toml               # Python project config (Smithery)
├── smithery.yaml                # Smithery runtime config
├── requirements.txt             # Python dependencies
├── .gitignore
├── src/                         # Smithery package structure
│   └── stealthee_mcp/
│       ├── __init__.py
│       └── server.py            # FastMCP server implementation
├── tools/                       # Tool schema definitions
│   ├── web_search.json
│   ├── url_extract.json
│   ├── score_signal.json
│   ├── batch_score_signals.json
│   ├── search_tech_sites.json
│   ├── parse_fields.json
│   └── run_pipeline.json
├── .smithery/                   # Smithery configuration (legacy)
│   └── manifest.json
├── data/                        # Data storage
│   └── signals.db              # SQLite database
├── testing/                     # Testing utilities
│   ├── validate_config.py
│   ├── test_fastapi.py
│   ├── monitor_logs.sh
│   ├── debug_mcp.sh
│   ├── validate_server.sh
│   ├── test.sh
│   ├── developer_settings.json
│   └── test_run_pipeline.json
├── planning/                    # Development planning
│   └── checklist.md
└── README.md
```

## 🔧 Development

### Adding New Tools

1. Add tool definition to `mcp_server_stdio.py` (for stdio)
2. Add tool definition to `src/stealthee_mcp/server.py` (for FastMCP/Smithery)
3. Implement handler methods in both servers
4. Register in `execute_tool` method (stdio) and `@server.tool()` decorator (FastMCP)
5. Create JSON schema in `tools/`
6. Add FastAPI endpoint in `fastapi_server.py` (legacy)
7. Update Smithery manifest (legacy)

## 📄 License

MIT License

## Support

- **Issues**: Create an issue on [GitHub](https://github.com/rainbowgore/stealthee-MCP-tools/issues)
- **Documentation**: Check the API docs at `/docs`
- **Logs**: Monitor with `./testing/monitor_logs.sh`

---

**Built with 💜 for the builders spotting what others miss**
