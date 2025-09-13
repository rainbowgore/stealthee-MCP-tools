#!/usr/bin/env python3
"""
FastMCP Server for Stealth Launch Radar
Smithery-compatible MCP server using FastMCP
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback

from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field
import aiohttp
import sqlite3
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

class ConfigSchema(BaseModel):
    tavily_api_key: str = Field(..., description="Tavily API key for web search")
    openai_api_key: str = Field(..., description="OpenAI API key for AI scoring")
    nimble_api_key: Optional[str] = Field(None, description="Nimble API key for parsing")
    slack_webhook_url: Optional[str] = Field(None, description="Slack webhook for alerts")

@smithery.server(config_schema=ConfigSchema)
def create_server():
    """Create and return a FastMCP server instance with session config."""
    
    server = FastMCP(name="Stealth Launch Radar")

    # Initialize database
    def init_database():
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect("data/signals.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                title TEXT,
                html_excerpt TEXT,
                changelog TEXT,
                pricing TEXT,
                score REAL,
                confidence TEXT,
                reasoning TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    init_database()

    @server.tool()
    async def web_search(ctx: Context, query: str, num_results: int = 3) -> str:
        """Search the web for information about stealth product launches."""
        config = ctx.session_config
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config.tavily_api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "query": query,
                    "search_depth": "basic",
                    "include_answer": False,
                    "include_raw_content": False,
                    "max_results": num_results
                }
                
                async with session.post("https://api.tavily.com/search", 
                                     headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        results = result.get("results", [])
                        
                        formatted_results = []
                        for item in results:
                            formatted_results.append(f"**{item.get('title', 'No title')}**\n{item.get('content', 'No content')}\nURL: {item.get('url', 'No URL')}\n")
                        
                        return "\n".join(formatted_results)
                    else:
                        return f"❌ Search failed: HTTP {response.status}"
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"❌ Search error: {str(e)}"

    @server.tool()
    async def url_extract(ctx: Context, url: str, parsing_type: str = "plain_text", wait_time: int = 2) -> str:
        """Extract and clean text content from a given URL."""
        try:
            await asyncio.sleep(wait_time)  # Artificial delay
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Remove scripts and styles
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Get text and clean it
                        text = soup.get_text()
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        return f"**URL:** {url}\n**Content Type:** {response.headers.get('content-type', 'unknown')}\n**Extracted Text:**\n{text[:1000]}{'...' if len(text) > 1000 else ''}"
                    else:
                        return f"❌ Failed to fetch URL: HTTP {response.status}"
        except Exception as e:
            logger.error(f"URL extraction error: {e}")
            return f"❌ Extraction error: {str(e)}"

    @server.tool()
    async def score_signal(ctx: Context, signal_text: str, signal_title: str = "") -> str:
        """Score a textual signal for likelihood of being a stealth product launch."""
        config = ctx.session_config
        
        try:
            client = openai.OpenAI(api_key=config.openai_api_key)
            
            prompt = f"""
            Analyze this text for stealth product launch indicators:
            
            Title: {signal_title}
            Text: {signal_text}
            
            Rate the likelihood of this being a stealth product launch (0.0 to 1.0).
            Consider: stealth keywords, launch timing, product mentions, pricing changes, etc.
            
            Respond with JSON:
            {{
                "launch_likelihood": 0.85,
                "confidence": "High",
                "reasoning": "Brief explanation of why this appears to be a stealth launch"
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            return f"**Signal Analysis:**\n{result}"
            
        except Exception as e:
            logger.error(f"Signal scoring error: {e}")
            return f"❌ Scoring error: {str(e)}"

    @server.tool()
    async def search_tech_sites(ctx: Context, query: str, num_results: int = 5) -> str:
        """Search tech news sites and Product Hunt for stealth launches."""
        config = ctx.session_config
        
        tech_sites = [
            "site:techcrunch.com",
            "site:producthunt.com", 
            "site:venturebeat.com",
            "site:theverge.com",
            "site:arstechnica.com"
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config.tavily_api_key}",
                    "Content-Type": "application/json"
                }
                
                all_results = []
                for site in tech_sites:
                    data = {
                        "query": f"{query} {site}",
                        "search_depth": "basic",
                        "include_answer": False,
                        "include_raw_content": False,
                        "max_results": 2
                    }
                    
                    async with session.post("https://api.tavily.com/search", 
                                         headers=headers, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            all_results.extend(result.get("results", []))
                
                # Format results
                formatted_results = []
                for item in all_results[:num_results]:
                    formatted_results.append(f"**{item.get('title', 'No title')}**\n{item.get('content', 'No content')}\nURL: {item.get('url', 'No URL')}\n")
                
                return "\n".join(formatted_results)
                
        except Exception as e:
            logger.error(f"Tech sites search error: {e}")
            return f"❌ Search error: {str(e)}"

    @server.tool()
    async def batch_score_signals(ctx: Context, signals: List[Dict[str, str]]) -> str:
        """Score multiple signals for stealth launch likelihood in batch."""
        config = ctx.session_config
        
        try:
            client = openai.OpenAI(api_key=config.openai_api_key)
            
            # Prepare batch prompt
            signals_text = []
            for i, signal in enumerate(signals, 1):
                title = signal.get('signal_title', f'Signal {i}')
                text = signal.get('signal_text', '')
                signals_text.append(f"Signal {i}: {title}\n{text}\n")
            
            prompt = f"""
            Analyze these signals for stealth product launch indicators:
            
            {''.join(signals_text)}
            
            For each signal, rate the likelihood of being a stealth product launch (0.0 to 1.0).
            Consider: stealth keywords, launch timing, product mentions, pricing changes, etc.
            
            Respond with JSON array:
            [
                {{
                    "signal_id": 1,
                    "launch_likelihood": 0.85,
                    "confidence": "High",
                    "reasoning": "Brief explanation"
                }},
                ...
            ]
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            return f"**Batch Signal Analysis:**\n{result}"
            
        except Exception as e:
            logger.error(f"Batch scoring error: {e}")
            return f"❌ Batch scoring error: {str(e)}"

    @server.tool()
    async def parse_fields(ctx: Context, html: str, target_fields: List[str] = None) -> str:
        """Extract structured stealth-launch indicators from raw HTML using Nimble's AI Parsing Skills."""
        if target_fields is None:
            target_fields = ["pricing", "changelog", "launch_announcement"]
            
        config = ctx.session_config
        
        if not config.nimble_api_key:
            return "❌ Nimble API key not configured"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config.nimble_api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "html": html,
                    "fields": target_fields
                }
                
                async with session.post("https://api.nimbleparser.com/parse", 
                                     headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        parsed_fields = result.get("parsed_fields", {})
                        
                        formatted_fields = []
                        for field, value in parsed_fields.items():
                            if value:
                                formatted_fields.append(f"**{field.title()}:** {value}")
                        
                        return f"**Parsed Fields:**\n" + "\n".join(formatted_fields) if formatted_fields else "No fields extracted"
                    else:
                        return f"❌ Parsing failed: HTTP {response.status}"
        except Exception as e:
            logger.error(f"Field parsing error: {e}")
            return f"❌ Parsing error: {str(e)}"

    @server.tool()
    async def run_pipeline(ctx: Context, query: str, num_results: int = 5, target_fields: List[str] = None) -> str:
        """End-to-end detection pipeline for stealth product launches."""
        if target_fields is None:
            target_fields = ["pricing", "changelog"]
            
        config = ctx.session_config
        
        try:
            logger.info(f"[Pipeline] Starting pipeline for query: {query}")
            
            # Step 1: Search tech sites
            search_results = await search_tech_sites(ctx, query, num_results)
            logger.info(f"[Pipeline] Search completed")
            
            # Step 2: Extract URLs and analyze
            results = []
            lines = search_results.split('\n')
            current_result = {}
            
            for line in lines:
                if line.startswith('**') and line.endswith('**'):
                    if current_result:
                        results.append(current_result)
                    current_result = {'title': line.strip('*'), 'content': '', 'url': ''}
                elif line.startswith('URL:'):
                    current_result['url'] = line.replace('URL:', '').strip()
                elif line and not line.startswith('**'):
                    current_result['content'] += line + ' '
            
            if current_result:
                results.append(current_result)
            
            logger.info(f"[Pipeline] Found {len(results)} results")
            
            # Step 3: Process each result
            processed_results = []
            for i, result in enumerate(results[:num_results]):
                if result.get('url'):
                    logger.info(f"[Pipeline] Processing result {i+1}: {result.get('title', 'No title')}")
                    
                    # Extract content from URL
                    extracted = await url_extract(ctx, result['url'])
                    
                    # Parse fields if Nimble is available
                    parsed_fields = ""
                    if config.nimble_api_key:
                        parsed_fields = await parse_fields(ctx, extracted, target_fields)
                    
                    # Score the signal
                    signal_text = f"{result.get('title', '')} {result.get('content', '')} {extracted}"
                    score_result = await score_signal(ctx, signal_text, result.get('title', ''))
                    
                    processed_results.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'score': score_result,
                        'extracted': extracted,
                        'parsed_fields': parsed_fields
                    })
            
            # Step 4: Format final results
            formatted_results = []
            for result in processed_results:
                formatted_results.append(f"**{result['title']}**\nURL: {result['url']}\n{result['score']}\n{result['parsed_fields']}\n---")
            
            logger.info(f"[Pipeline] Pipeline completed successfully")
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return f"❌ Pipeline error: {str(e)}"

    return server
