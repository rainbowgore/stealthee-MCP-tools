#!/bin/bash
# Startup script for Smithery development

echo "🚀 Starting Stealth Launch Radar for Smithery"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "📦 Installing FastAPI dependencies..."
    pip install fastapi uvicorn pydantic
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << EOF
# Required API Keys
TAVILY_API_KEY=your_tavily_key_here
OPENAI_API_KEY=your_openai_key_here

# Optional
NIMBLE_API_KEY=your_nimble_key_here
SLACK_WEBHOOK_URL=your_slack_webhook_here
EOF
    echo "📝 Please edit .env file with your API keys"
    exit 1
fi

echo "✅ Environment ready"
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔧 Smithery manifest: .smithery/manifest.json"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start the server
python start_fastapi.py
