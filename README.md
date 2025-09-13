# Stealthee MCP - Be Early

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-Server-4b8bbe)](https://github.com/nimbleai/mcp)
[![OpenAI API](https://img.shields.io/badge/OpenAI-Integrated-orange)](https://platform.openai.com/)
[![Tavily](https://img.shields.io/badge/Tavily-Search-green)](https://docs.tavily.com/)
[![Nimble](https://img.shields.io/badge/Nimble-AI%20Parsing-purple)](https://docs.nimbleai.dev/)
[![Slack Alerts](https://img.shields.io/badge/Slack-Alerts%20Enabled-4A154B?logo=slack)](https://slack.com/)
[![Smithery](https://img.shields.io/badge/Smithery-Compatible-%23007acc)](https://smithery.tools/)

Stealthee is a dev-first system for surfacing pre-public product signals - before they trend.
It combines search, extraction, scoring, and alerting into a plug-and-play pipeline you can integrate into Claude, LangGraph, Smithery, or your own AI stack via MCP.

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

## 🛠️ Installation

### Prerequisites

- Python 3.8+
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

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start MCP Server**

   ```bash
   python mcp_server_stdio.py
   ```

4. **Start FastAPI Server** (Optional)
   ```bash
   python start_fastapi.py
   # Or for Smithery compatibility:
   ./start_smithery.sh
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
TAVILY_API_KEY=your_tavily_key_here
OPENAI_API_KEY=your_openai_key_here

# Optional
NIMBLE_API_KEY=your_nimble_key_here
SLACK_WEBHOOK_URL=your_slack_webhook_here
```

### Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "stealth-mcp": {
      "command": "/path/to/stealthee-MCP-tools/.venv/bin/python",
      "args": ["/path/to/stealthee-MCP-tools/mcp_server_stdio.py"],
      "cwd": "/path/to/stealthed",
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

The MCP server provides tools that can be used directly in Claude Desktop:

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

### Smithery Integration

The tool is compatible with [Smithery](https://smithery.sh):

```bash
# Start Smithery development server
smithery dev

# Or use the provided script
./start_smithery.sh
```

## 🏗️ Architecture

### MCP Server (`mcp_server_stdio.py`)

- Implements Model Context Protocol over stdio
- Provides 7 core tools for stealth detection
- Handles JSON-RPC communication with Claude Desktop
- Includes SQLite database for signal storage

### FastAPI Server (`fastapi_server.py`)

- Exposes MCP tools as HTTP endpoints
- Compatible with Smithery and other AI agent platforms
- Includes request/response logging
- Provides OpenAPI documentation

### Tool Schemas (`tools/`)

- JSON schema definitions for all tools
- Input/output validation
- Example usage patterns

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

## 📊 Database Schema

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

## 🧪 Testing

### MCP Server Testing

```bash
# Test MCP server startup
python testing/validate_config.py

# Monitor logs
./testing/monitor_logs.sh
```

### FastAPI Testing

```bash
# Test API endpoints
python testing/test_fastapi.py

# Test specific pipeline
curl -X POST "http://localhost:8000/tools/run_pipeline" \
  -H "Content-Type: application/json" \
  -d @testing/test_run_pipeline.json
```

## 📁 Project Structure

```
stealthee-MCP-tools/
├── mcp_server_stdio.py          # Main MCP server
├── fastapi_server.py            # FastAPI server
├── start_fastapi.py             # FastAPI startup script
├── start_smithery.sh            # Smithery startup script
├── requirements.txt             # Python dependencies
├── .gitignore                  # Git ignore rules
├── tools/                      # Tool schema definitions
│   ├── web_search.json
│   ├── url_extract.json
│   ├── score_signal.json
│   ├── batch_score_signals.json
│   ├── search_tech_sites.json
│   ├── parse_fields.json
│   └── run_pipeline.json
├── .smithery/                  # Smithery configuration
│   └── manifest.json
├── data/                       # Data storage
│   └── signals.db             # SQLite database
├── testing/                    # Testing utilities
│   ├── validate_config.py
│   ├── test_fastapi.py
│   ├── monitor_logs.sh
│   └── test_run_pipeline.json
└── README.md                   # This file
```

## 🔧 Development

### Adding New Tools

1. Add tool definition to `mcp_server_stdio.py`
2. Implement handler method
3. Register in `execute_tool` method
4. Create JSON schema in `tools/`
5. Add FastAPI endpoint in `fastapi_server.py`
6. Update Smithery manifest

### Dependencies

The project uses minimal, focused dependencies:

- `aiohttp` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `openai` - AI scoring
- `python-dotenv` - Environment variables
- `fastapi` - HTTP API server
- `uvicorn` - ASGI server
- `pydantic` - Data validation

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues**: Create an issue on [GitHub](https://github.com/rainbowgore/stealthee-MCP-tools/issues)
- **Documentation**: Check the API docs at `/docs`
- **Logs**: Monitor with `./testing/monitor_logs.sh`

---

**Built with 💜 for the builders spotting what others miss**
