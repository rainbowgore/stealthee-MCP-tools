#!/usr/bin/env python3
"""
FastAPI Server for Stealth Launch Radar
Exposes MCP tools via HTTP endpoints for Smithery compatibility
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

# Import the MCP server class and handlers
from mcp_server_stdio import MCPStdioServer

# Smithery compatibility
try:
    from smithery.decorators import smithery
    SMITHERY_AVAILABLE = True
except ImportError:
    SMITHERY_AVAILABLE = False
    # Create a dummy decorator if Smithery is not available
    def smithery():
        def decorator(func):
            return func
        return decorator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
@smithery.server()
def create_app():
    return FastAPI(
        title="Stealth Launch Radar API",
        description="API for detecting stealth product launches using AI-powered analysis",
        version="1.0.0"
    )

# Create the app instance
app = create_app()

# Initialize MCP server instance
mcp_server = MCPStdioServer()

# Pydantic models for request/response
class MCPResponse(BaseModel):
    content: List[Dict[str, Any]]
    isError: bool = False

class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for stealth launches")
    num_results: int = Field(3, description="Number of results to return")

class URLExtractRequest(BaseModel):
    url: str = Field(..., description="URL to extract content from")
    parsing_type: str = Field("plain_text", description="Type of parsing (plain_text or html)")

class ScoreSignalRequest(BaseModel):
    signal_text: str = Field(..., description="Text content of the signal to score")
    signal_title: str = Field("", description="Title of the signal")

class BatchScoreSignalsRequest(BaseModel):
    signals: List[Dict[str, str]] = Field(..., description="Array of signals to score")

class SearchTechSitesRequest(BaseModel):
    query: str = Field(..., description="Search query for tech news")
    num_results: int = Field(3, ge=1, le=10, description="Number of results to return")

class ParseFieldsRequest(BaseModel):
    html: str = Field(..., description="Raw HTML content to parse")
    target_fields: List[str] = Field(["pricing", "changelog"], description="List of fields to extract")

class RunPipelineRequest(BaseModel):
    query: str = Field(..., description="Search query to detect stealth launches")
    num_results: int = Field(5, description="Number of search results to analyze")
    target_fields: List[str] = Field(["pricing", "changelog"], description="Fields to extract from HTML")

# Middleware for logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Tool endpoints
@app.post("/tools/web_search", response_model=MCPResponse)
async def web_search(request: WebSearchRequest):
    """Search the web for information about stealth product launches"""
    try:
        logger.info(f"Web search request: {request.query}")
        result = await mcp_server._web_search_handler(request.dict())
        return MCPResponse(content=result, isError=False)
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return MCPResponse(
            content=[{"type": "text", "text": f"❌ Web search failed: {str(e)}"}],
            isError=True
        )

@app.post("/tools/url_extract", response_model=MCPResponse)
async def url_extract(request: URLExtractRequest):
    """Extract content from a URL for analysis"""
    try:
        logger.info(f"URL extract request: {request.url}")
        result = await mcp_server._url_extract_handler(request.dict())
        return MCPResponse(content=result, isError=False)
    except Exception as e:
        logger.error(f"URL extract error: {e}")
        return MCPResponse(
            content=[{"type": "text", "text": f"❌ URL extraction failed: {str(e)}"}],
            isError=True
        )

@app.post("/tools/score_signal", response_model=MCPResponse)
async def score_signal(request: ScoreSignalRequest):
    """Score a signal for launch likelihood using AI"""
    try:
        logger.info(f"Score signal request: {request.signal_title}")
        result = await mcp_server._score_signal_handler(request.dict())
        return MCPResponse(content=result, isError=False)
    except Exception as e:
        logger.error(f"Score signal error: {e}")
        return MCPResponse(
            content=[{"type": "text", "text": f"❌ Signal scoring failed: {str(e)}"}],
            isError=True
        )

@app.post("/tools/batch_score_signals", response_model=MCPResponse)
async def batch_score_signals(request: BatchScoreSignalsRequest):
    """Score multiple signals for stealth launch likelihood in batch"""
    try:
        logger.info(f"Batch score signals request: {len(request.signals)} signals")
        result = await mcp_server._batch_score_signals_handler(request.dict())
        return MCPResponse(content=result, isError=False)
    except Exception as e:
        logger.error(f"Batch score signals error: {e}")
        return MCPResponse(
            content=[{"type": "text", "text": f"❌ Batch signal scoring failed: {str(e)}"}],
            isError=True
        )

@app.post("/tools/search_tech_sites", response_model=MCPResponse)
async def search_tech_sites(request: SearchTechSitesRequest):
    """Search tech news sites for stealth product launches"""
    try:
        logger.info(f"Search tech sites request: {request.query}")
        result = await mcp_server._search_tech_sites_handler(request.dict())
        return MCPResponse(content=result, isError=False)
    except Exception as e:
        logger.error(f"Search tech sites error: {e}")
        return MCPResponse(
            content=[{"type": "text", "text": f"❌ Tech sites search failed: {str(e)}"}],
            isError=True
        )

@app.post("/tools/parse_fields", response_model=MCPResponse)
async def parse_fields(request: ParseFieldsRequest):
    """Extract structured stealth-launch indicators from raw HTML using Nimble's AI Parsing Skills"""
    try:
        logger.info(f"Parse fields request: {len(request.target_fields)} fields")
        result = await mcp_server._parse_fields_handler(request.dict())
        return MCPResponse(content=result, isError=False)
    except Exception as e:
        logger.error(f"Parse fields error: {e}")
        return MCPResponse(
            content=[{"type": "text", "text": f"❌ Field parsing failed: {str(e)}"}],
            isError=True
        )

@app.post("/tools/run_pipeline", response_model=MCPResponse)
async def run_pipeline(request: RunPipelineRequest):
    """End-to-end detection pipeline for stealth product launches"""
    try:
        logger.info(f"Run pipeline request: {request.query}")
        result = await mcp_server._run_pipeline_handler(request.dict())
        return MCPResponse(content=result, isError=False)
    except Exception as e:
        logger.error(f"Run pipeline error: {e}")
        return MCPResponse(
            content=[{"type": "text", "text": f"❌ Pipeline failed: {str(e)}"}],
            isError=True
        )

# Tools list endpoint
@app.get("/tools")
async def list_tools():
    """List all available tools"""
    return {
        "tools": list(mcp_server.tools.values()),
        "count": len(mcp_server.tools)
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Stealth Launch Radar API",
        "version": "1.0.0",
        "tools": list(mcp_server.tools.keys()),
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
