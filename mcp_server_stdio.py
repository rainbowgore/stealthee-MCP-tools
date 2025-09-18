#!/usr/bin/env python3
"""
MCP-Compliant Server for Stealth Launch Radar
Implements proper MCP protocol with JSON-RPC over stdio
"""
import asyncio
import json
import logging
import sys
import os
import aiohttp
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv
import re  # Add missing import

# Load environment variables from .env file
load_dotenv()

# Configure logging to stderr for MCP
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

class MCPStdioServer:
    def __init__(self):
        # Initialize database
        self._init_database()
        
        self.tools = {
            "web_search": {
                "name": "web_search",
                "description": "Search the web for information about stealth product launches",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for stealth launches"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            },
            "url_extract": {
                "name": "url_extract",
                "description": "Extract content from a URL for analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to extract content from"
                        },
                        "parsing_type": {
                            "type": "string",
                            "description": "Type of parsing (plain_text or html)",
                            "default": "plain_text"
                        }
                    },
                    "required": ["url"]
                }
            },
            "score_signal": {
                "name": "score_signal",
                "description": "Score a signal for launch likelihood using AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "signal_text": {
                            "type": "string",
                            "description": "Text content of the signal to score"
                        },
                        "signal_title": {
                            "type": "string",
                            "description": "Title of the signal",
                            "default": ""
                        }
                    },
                    "required": ["signal_text"]
                }
            },
            "search_tech_sites": {
                "name": "search_tech_sites",
                "description": "Search tech news sites for stealth product launches",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for tech news"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 3,
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["query"]
                }
            },
            "parse_fields": {
                "name": "parse_fields",
                "description": "Extract structured stealth-launch indicators from raw HTML using Nimble's AI Parsing Skills",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "html": {
                            "type": "string",
                            "description": "Raw HTML content to parse"
                        },
                        "target_fields": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of fields to extract (e.g. ['pricing', 'changelog', 'launch_announcement'])"
                        }
                    },
                    "required": ["html"]
                }
            },
            "batch_score_signals": {
                "name": "batch_score_signals",
                "description": "Score multiple signals for stealth launch likelihood in batch",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "signals": {
                            "type": "array",
                            "description": "Array of signals to score",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "signal_text": {
                                        "type": "string",
                                        "description": "Text content of the signal"
                                    },
                                    "signal_title": {
                                        "type": "string",
                                        "description": "Title or identifier for the signal",
                                        "default": ""
                                    }
                                },
                                "required": ["signal_text"]
                            },
                            "minItems": 1,
                            "maxItems": 20
                        }
                    },
                    "required": ["signals"]
                }
            },
            "run_pipeline": {
                "name": "run_pipeline",
                "description": "End-to-end detection pipeline for stealth product launches",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to detect stealth launches"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of search results to analyze",
                            "default": 5
                        },
                        "target_fields": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Fields to extract from HTML, e.g. ['pricing', 'changelog']",
                            "default": ["pricing", "changelog"]
                        }
                    },
                    "required": ["query"]
                }
            }
        }
        logger.info(f"Loaded {len(self.tools)} tools")

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP JSON-RPC requests"""
        try:
            method = request.get("method")
            request_id = request.get("id")
            
            # Ensure id is always a string
            if request_id is not None:
                request_id = str(request_id)
            else:
                request_id = "unknown"
            
            logger.info(f"Handling MCP request: {method}")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {
                                "listChanged": False
                            }
                        },
                        "serverInfo": {
                            "name": "stealth-launch-radar",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": list(self.tools.values())
                    }
                }
            
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name not in self.tools:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{tool_name}' not found"
                        }
                    }
                
                # Execute the tool
                result = await self.execute_tool(tool_name, arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": result,
                        "isError": False
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            error_id = request.get("id")
            if error_id is not None:
                error_id = str(error_id)
            else:
                error_id = "unknown"
            return {
                "jsonrpc": "2.0",
                "id": error_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    async def  execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a tool and return MCP-compliant results"""
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")
        
        try:
            if tool_name == "web_search":
                return await self._web_search_handler(arguments)
            elif tool_name == "url_extract":
                return await self._url_extract_handler(arguments)
            elif tool_name == "score_signal":
                return await self._score_signal_handler(arguments)
            elif tool_name == "search_tech_sites":
                return await self._search_tech_sites_handler(arguments)
            elif tool_name == "batch_score_signals":
                return await self._batch_score_signals_handler(arguments)
            elif tool_name == "parse_fields":
                return await self._parse_fields_handler(arguments)
            elif tool_name == "run_pipeline":
                return await self._run_pipeline_handler(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return [{
                "type": "text",
                "text": f"❌ Error executing {tool_name}: {str(e)}"
            }]

    async def _web_search_handler(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle web search using Tavily API"""
        query = arguments.get("query", "")
        num_results = arguments.get("num_results", 3)
        
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            logger.error("TAVILY_API_KEY environment variable not set")
            return [{
                "type": "text",
                "text": "❌ Error: TAVILY_API_KEY environment variable not set"
            }]
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": query,
                    "search_depth": "basic",
                    "include_answer": False,
                    "include_raw_content": False,
                    "max_results": num_results
                }
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    "https://api.tavily.com/search",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"Tavily API error: {response.status}")
                        return [{
                            "type": "text",
                            "text": f"❌ Error: Tavily API returned status {response.status}"
                        }]
                    
                    data = await response.json()
                    results = data.get("results", [])
                    
                    if not results:
                        return [{
                            "type": "text",
                            "text": f"🔍 No results found for query: '{query}'"
                        }]
                    
                    formatted_results = []
                    for i, result in enumerate(results[:num_results], 1):
                        formatted_results.append({
                            "type": "text",
                            "text": f"🔍 Result {i}:\nTitle: {result.get('title', 'N/A')}\nURL: {result.get('url', 'N/A')}\nSnippet: {result.get('content', 'N/A')}\n"
                        })
                    
                    return formatted_results
                    
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return [{
                "type": "text",
                "text": f"❌ Web search failed: {str(e)}"
            }]

    async def _url_extract_handler(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle URL content extraction"""
        url = arguments.get("url", "")
        parsing_type = arguments.get("parsing_type", "plain_text")
        wait_time = arguments.get("wait_time", 2)
        
        try:
            # Add artificial delay
            await asyncio.sleep(wait_time)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"HTTP error {response.status} for URL: {url}")
                        return [{
                            "type": "text",
                            "text": f"❌ Error: HTTP {response.status} for URL: {url}"
                        }]
                    
                    html_content = await response.text()
                    content_type = response.headers.get('content-type', 'unknown')
                    
                    # Extract title from HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    title = soup.find('title')
                    title_text = title.get_text().strip() if title else "No title found"
                    
                    if parsing_type == "html":
                        # Return raw HTML
                        cleaned_content = html_content
                    else:
                        # Extract plain text
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Get text and clean up whitespace
                        text = soup.get_text()
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        cleaned_content = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    return [{
                        "type": "text",
                        "text": f"📄 URL Extraction Results:\n\nURL: {url}\nTitle: {title_text}\nContent Type: {content_type}\nExtracted At: {datetime.now().isoformat()}\n\nContent:\n{cleaned_content[:2000]}{'...' if len(cleaned_content) > 2000 else ''}"
                    }]
                    
        except Exception as e:
            logger.error(f"URL extraction error: {e}")
            return [{
                "type": "text",
                "text": f"❌ URL extraction failed: {str(e)}"
            }]

    async def _score_signal_handler(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle signal scoring using OpenAI API"""
        signal_text = arguments.get("signal_text", "")
        signal_title = arguments.get("signal_title", "")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            return [{
                "type": "text",
                "text": "❌ Error: OPENAI_API_KEY environment variable not set"
            }]
        
        try:
            client = openai.AsyncOpenAI(api_key=api_key)
            
            prompt = f"""Analyze the following text for indicators of a stealth product launch. Provide your analysis in JSON format with these exact fields:
- launch_likelihood: a number between 0 and 1 (0 = definitely not a stealth launch, 1 = definitely a stealth launch)
- confidence: one of "Low", "Medium", or "High"
- reasoning: 2-3 sentences explaining your assessment

Text to analyze:
Title: {signal_title}
Content: {signal_text}

Look for indicators like:
- Mentions of "stealth mode", "quiet launch", "beta", "pilot"
- Product announcements without fanfare
- Funding announcements with product mentions
- Team hiring for specific products
- Patent filings or trademark applications
- Partnership announcements with new products

Respond with valid JSON only:"""

            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at detecting stealth product launches from text signals. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse the JSON response
            try:
                result_data = json.loads(result_text)
                launch_likelihood = result_data.get("launch_likelihood", 0.0)
                confidence = result_data.get("confidence", "Low")
                reasoning = result_data.get("reasoning", "No reasoning provided")
                
                return [{
                    "type": "text",
                    "text": f"🎯 Signal Analysis Results:\n\nTitle: {signal_title}\nText Preview: {signal_text[:200]}{'...' if len(signal_text) > 200 else ''}\n\nLaunch Likelihood: {launch_likelihood:.2f}/1.0\nConfidence: {confidence}\nReasoning: {reasoning}\n\nAnalysis completed at: {datetime.now().isoformat()}"
                }]
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return [{
                    "type": "text",
                    "text": f"🎯 Signal Analysis Results:\n\nTitle: {signal_title}\nText Preview: {signal_text[:200]}{'...' if len(signal_text) > 200 else ''}\n\nRaw AI Response: {result_text}\n\nAnalysis completed at: {datetime.now().isoformat()}"
                }]
                
        except Exception as e:
            logger.error(f"Signal scoring error: {e}")
            return [{
                "type": "text",
                "text": f"❌ Signal scoring failed: {str(e)}"
            }]

    async def _search_tech_sites_handler(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle tech sites search using Tavily API with domain filtering"""
        query = arguments.get("query", "")
        num_results = arguments.get("num_results", 3)
        
        # Define tech news sites to search
        tech_domains = [
            "techcrunch.com",
            "theverge.com", 
            "wired.com",
            "arstechnica.com",
            "ycombinator.com",
            "producthunt.com",
            "betalist.com",
            "venturebeat.com",
            "recode.net",
            "mashable.com",
            "engadget.com",
            "gizmodo.com",
            "techradar.com",
            "zdnet.com",
            "cnet.com"
        ]
        
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            logger.error("TAVILY_API_KEY environment variable not set")
            return [{
                "type": "text",
                "text": "❌ Error: TAVILY_API_KEY environment variable not set"
            }]
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": query,
                    "search_depth": "basic",
                    "include_answer": False,
                    "include_raw_content": False,
                    "max_results": num_results,
                    "include_domains": tech_domains  # This filters to only tech sites
                }
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    "https://api.tavily.com/search",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"Tavily API error: {response.status}")
                        return [{
                            "type": "text",
                            "text": f"❌ Error: Tavily API returned status {response.status}"
                        }]
                    
                    data = await response.json()
                    results = data.get("results", [])
                    
                    if not results:
                        return [{
                            "type": "text",
                            "text": f"🔍 No results found for query: '{query}' in tech news sites"
                        }]
                    
                    formatted_results = []
                    for i, result in enumerate(results[:num_results], 1):
                        formatted_results.append({
                            "type": "text",
                            "text": f"�� Tech News Result {i}:\nTitle: {result.get('title', 'N/A')}\nURL: {result.get('url', 'N/A')}\nSnippet: {result.get('content', 'N/A')}\n"
                        })
                    
                    return formatted_results
                    
        except Exception as e:
            logger.error(f"Tech sites search error: {e}")
            return [{
                "type": "text",
                "text": f"❌ Tech sites search failed: {str(e)}"
            }]

    async def _batch_score_signals_handler(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle batch scoring of multiple signals using OpenAI API"""
        signals = arguments.get("signals", [])
        
        if not signals:
            return [{
                "type": "text",
                "text": "❌ Error: No signals provided for batch scoring"
            }]
        
        if len(signals) > 20:
            return [{
                "type": "text",
                "text": "❌ Error: Too many signals. Maximum 20 signals per batch."
            }]
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            return [{
                "type": "text",
                "text": "❌ Error: OPENAI_API_KEY environment variable not set"
            }]
        
        try:
            client = openai.AsyncOpenAI(api_key=api_key)
            
            # Prepare signals for batch processing
            signals_text = ""
            for i, signal in enumerate(signals, 1):
                title = signal.get("signal_title", f"Signal {i}")
                text = signal.get("signal_text", "")
                signals_text += f"\n{i}. Title: {title}\nContent: {text}\n"
            
            prompt = f"""Analyze the following signals for indicators of stealth product launches. For each signal, provide your analysis in JSON format with these exact fields:
- signal_id: the number of the signal (1, 2, 3, etc.)
- launch_likelihood: a number between 0 and 1 (0 = definitely not a stealth launch, 1 = definitely a stealth launch)
- confidence: one of "Low", "Medium", or "High"
- reasoning: 2-3 sentences explaining your assessment

Signals to analyze:
{signals_text}

Look for indicators like:
- Mentions of "stealth mode", "quiet launch", "beta", "pilot"
- Product announcements without fanfare
- Funding announcements with product mentions
- Team hiring for specific products
- Patent filings or trademark applications
- Partnership announcements with new products

Respond with valid JSON array format:
[
  {{"signal_id": 1, "launch_likelihood": 0.85, "confidence": "High", "reasoning": "..."}},
  {{"signal_id": 2, "launch_likelihood": 0.15, "confidence": "High", "reasoning": "..."}}
]"""

            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at detecting stealth product launches from text signals. Always respond with valid JSON array format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse the JSON response
            try:
                results_data = json.loads(result_text)
                
                # Format the results
                formatted_results = []
                for i, result in enumerate(results_data):
                    signal = signals[i] if i < len(signals) else {}
                    signal_title = signal.get("signal_title", f"Signal {i+1}")
                    signal_text = signal.get("signal_text", "")
                    
                    formatted_results.append({
                        "type": "text",
                        "text": f"🎯 Signal {i+1} Analysis:\n\nTitle: {signal_title}\nText Preview: {signal_text[:100]}{'...' if len(signal_text) > 100 else ''}\n\nLaunch Likelihood: {result.get('launch_likelihood', 0.0):.2f}/1.0\nConfidence: {result.get('confidence', 'Unknown')}\nReasoning: {result.get('reasoning', 'No reasoning provided')}\n"
                    })
                
                # Add summary
                high_likelihood = sum(1 for r in results_data if r.get('launch_likelihood', 0) > 0.7)
                total_signals = len(results_data)
                
                formatted_results.append({
                    "type": "text",
                    "text": f"\n📊 Batch Analysis Summary:\nHigh likelihood signals: {high_likelihood}/{total_signals}\nAnalysis completed at: {datetime.now().isoformat()}"
                })
                
                return formatted_results
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return [{
                    "type": "text",
                    "text": f"🎯 Batch Signal Analysis Results:\n\nRaw AI Response: {result_text}\n\nAnalysis completed at: {datetime.now().isoformat()}"
                }]
                
        except Exception as e:
            logger.error(f"Batch signal scoring error: {e}")
            return [{
                "type": "text",
                "text": f"❌ Batch signal scoring failed: {str(e)}"
            }]

    async def _parse_fields_handler(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle field parsing using Nimble's AI Parsing Skills"""
        html = arguments.get("html", "")
        target_fields = arguments.get("target_fields", ["pricing", "changelog", "launch_announcement"])
        
        if not html:
            return [{
                "type": "text",
                "text": "❌ Error: No HTML content provided for parsing"
            }]
        
        api_key = os.getenv("NIMBLE_API_KEY")
        if not api_key:
            logger.error("NIMBLE_API_KEY environment variable not set")
            return [{
                "type": "text",
                "text": "❌ Error: NIMBLE_API_KEY environment variable not set. Please configure your API key."
            }]
        
        try:
            logger.info(f"Parsing fields from HTML: {target_fields}")
            
            # Make actual API call to Nimble AI Parsing Skills
            url = "https://api.nimble.com/parse-fields"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "html": html,
                "fields": target_fields
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Format the results
                        result_text = "�� Parsed Fields:\n\n"
                        for field in target_fields:
                            value = result.get(field, "No data found")
                            result_text += f"{field.title()}: {value}\n"
                        
                        return [{
                            "type": "text",
                            "text": result_text
                        }]
                    else:
                        error_text = await response.text()
                        logger.error(f"Nimble API error {response.status}: {error_text}")
                        return [{
                            "type": "text",
                            "text": f"❌ Nimble API error {response.status}: {error_text}"
                        }]
            
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling Nimble API: {e}")
            return [{
                "type": "text",
                "text": f"❌ Network error: {str(e)}"
            }]
        except Exception as e:
            logger.error(f"Field parsing error: {e}")
            return [{
                "type": "text",
                "text": f"❌ Field parsing failed: {str(e)}"
            }]

    async def _run_pipeline_handler(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle end-to-end stealth launch detection pipeline"""
        query = arguments.get("query", "")
        num_results = arguments.get("num_results", 5)
        target_fields = arguments.get("target_fields", ["pricing", "changelog"])
        
        logger.info(f"[Pipeline] Starting pipeline with query: '{query}'")
        logger.info(f"[Pipeline] Target results: {num_results}")
        logger.info(f"[Pipeline] Target fields: {target_fields}")
        
        if not query:
            logger.error("[Pipeline] No search query provided")
            return [{
                "type": "text",
                "text": "❌ Error: No search query provided for pipeline"
            }]
        
        try:
            # Step 1: Search tech sites
            logger.info("[Pipeline] Step 1: Searching tech sites...")
            search_results = await self._search_tech_sites_handler({
                "query": query,
                "num_results": num_results
            })
            
            if not search_results or not search_results[0].get("text"):
                logger.warning("[Pipeline] No search results found")
                return [{
                    "type": "text",
                    "text": "❌ No search results found for the query"
                }]
            
            logger.info(f"[Pipeline] Search completed, processing results...")
            
            # Parse search results to extract URLs
            search_text = search_results[0]["text"]
            urls = self._extract_urls_from_search_results(search_text)
            
            if not urls:
                logger.warning("[Pipeline] No URLs extracted from search results")
                return [{
                    "type": "text",
                    "text": "❌ No URLs found in search results"
                }]
            
            logger.info(f"[Pipeline] Found {len(urls)} URLs to analyze")
            for i, url in enumerate(urls, 1):
                logger.info(f"[Pipeline] URL {i}: {url}")
            
            # Step 2: Process each URL through the pipeline
            logger.info(f"[Pipeline] Step 2: Processing {min(len(urls), num_results)} URLs...")
            enriched_signals = []
            
            for i, url in enumerate(urls[:num_results], 1):
                try:
                    logger.info(f"[Pipeline] Processing URL {i}/{min(len(urls), num_results)}: {url}")
                    
                    # Extract content from URL
                    logger.info(f"[Pipeline] Extracting content from URL {i}...")
                    extract_result = await self._url_extract_handler({
                        "url": url,
                        "parsing_type": "html"
                    })
                    
                    if not extract_result or not extract_result[0].get("text"):
                        logger.warning(f"[Pipeline] Failed to extract content from URL {i}: {url}")
                        continue
                    
                    html_content = extract_result[0]["text"]
                    logger.info(f"[Pipeline] Extracted {len(html_content)} characters from URL {i}")
                    
                    # Parse fields from HTML
                    logger.info(f"[Pipeline] Parsing fields from URL {i}...")
                    parse_result = await self._parse_fields_handler({
                        "html": html_content,
                        "target_fields": target_fields
                    })
                    
                    if not parse_result or not parse_result[0].get("text"):
                        logger.warning(f"[Pipeline] Failed to parse fields from URL {i}: {url}")
                        continue
                    
                    parsed_fields = parse_result[0]["text"]
                    logger.info(f"[Pipeline] Parsed fields from URL {i}: {parsed_fields[:100]}...")
                    
                    # Build combined signal
                    signal = {
                        "signal_title": f"Stealth Launch Signal {i}",
                        "signal_text": f"URL: {url}\n\nExtracted Content:\n{html_content[:500]}...\n\nParsed Fields:\n{parsed_fields}"
                    }
                    
                    enriched_signals.append(signal)
                    logger.info(f"[Pipeline] Successfully processed URL {i} - Signal added to batch")
                    
                except Exception as e:
                    logger.error(f"[Pipeline] Error processing URL {i} ({url}): {e}")
                    continue
            
            if not enriched_signals:
                logger.error("[Pipeline] No signals could be processed successfully")
                return [{
                    "type": "text",
                    "text": "❌ No signals could be processed successfully"
                }]
            
            logger.info(f"[Pipeline] Successfully processed {len(enriched_signals)} signals")
            
            # Step 3: Batch score all signals
            logger.info(f"[Pipeline] Step 3: Batch scoring {len(enriched_signals)} signals...")
            scoring_result = await self._batch_score_signals_handler({
                "signals": enriched_signals
            })
            
            if not scoring_result:
                logger.error("[Pipeline] Failed to score signals")
                return [{
                    "type": "text",
                    "text": "❌ Failed to score signals"
                }]
            
            logger.info(f"[Pipeline] Batch scoring completed - {len(scoring_result)} results received")
            
            # Step 4: Parse scoring results and send Slack alerts
            logger.info("[Pipeline] Step 4: Processing scoring results and sending alerts...")
            results = []
            
            # Parse scoring results to extract scores and send alerts
            high_confidence_signals = []
            logger.info(f"[Pipeline] Analyzing {len(scoring_result)} scoring results...")
            
            for i, scoring_text in enumerate(scoring_result):
                if "Launch Likelihood:" in scoring_text.get("text", ""):
                    # Extract score from the text
                    score_match = re.search(r"Launch Likelihood: ([\d.]+)", scoring_text["text"])
                    if score_match:
                        score = float(score_match.group(1))
                        logger.info(f"[Pipeline] Signal {i+1} scored: {score:.2f}")
                        
                        # Store signal in database regardless of score
                        signal_index = i
                        if signal_index < len(enriched_signals):
                            signal = enriched_signals[signal_index]
                            url = urls[signal_index] if signal_index < len(urls) else "Unknown URL"
                            
                            # Extract fields from the signal text
                            fields = {}
                            if "Parsed Fields:" in signal["signal_text"]:
                                # Parse the fields from the signal text
                                fields_text = signal["signal_text"].split("Parsed Fields:")[-1].strip()
                                for field in target_fields:
                                    if field.title() in fields_text:
                                        # Extract the value after the field name
                                        field_pattern = rf"{field.title()}: ([^\n]+)"
                                        field_match = re.search(field_pattern, fields_text)
                                        if field_match:
                                            fields[field] = field_match.group(1).strip()
                            
                            # Extract confidence and reasoning from scoring text
                            confidence = "Unknown"
                            reasoning = "No reasoning provided"
                            
                            if "Confidence:" in scoring_text["text"]:
                                conf_match = re.search(r"Confidence: ([^\n]+)", scoring_text["text"])
                                if conf_match:
                                    confidence = conf_match.group(1).strip()
                            
                            if "Reasoning:" in scoring_text["text"]:
                                reason_match = re.search(r"Reasoning: ([^\n]+)", scoring_text["text"])
                                if reason_match:
                                    reasoning = reason_match.group(1).strip()
                            
                            # Prepare signal data for database
                            signal_data = {
                                "url": url,
                                "title": signal["signal_title"],
                                "html_excerpt": signal["signal_text"][:500],  # First 500 characters
                                "changelog": fields.get("changelog", ""),
                                "pricing": fields.get("pricing", ""),
                                "score": score,
                                "confidence": confidence,
                                "reasoning": reasoning,
                                "created_at": datetime.now().isoformat()
                            }
                            
                            # Store in database
                            logger.info(f"[Pipeline] Storing signal {i+1} in database...")
                            db_success = self.store_signal(signal_data)
                            if db_success:
                                logger.info(f"[Pipeline] ✅ Signal {i+1} stored in database")
                            else:
                                logger.warning(f"[Pipeline] ⚠️ Failed to store signal {i+1} in database")
                            
                            # Handle high-confidence signals for Slack alerts
                            if score >= 0.75:
                                logger.info(f"[Pipeline] High-confidence signal detected! Score: {score:.2f}")
                                logger.info(f"[Pipeline] Signal title: {signal['signal_title']}")
                                logger.info(f"[Pipeline] Signal URL: {url}")
                                logger.info(f"[Pipeline] Extracted fields: {fields}")
                                
                                # Send Slack alert
                                logger.info(f"[Pipeline] Sending Slack alert for high-confidence signal...")
                                alert_sent = await self.send_slack_alert(
                                    title=signal["signal_title"],
                                    score=score,
                                    url=url,
                                    fields=fields
                                )
                                
                                if alert_sent:
                                    high_confidence_signals.append(f"Signal {signal_index + 1} (Score: {score:.2f})")
                                    logger.info(f"[Pipeline] ✅ Slack alert sent successfully for: {signal['signal_title']}")
                                else:
                                    logger.warning(f"[Pipeline] ⚠️ Failed to send Slack alert for: {signal['signal_title']}")
                            else:
                                logger.info(f"[Pipeline] Signal {i+1} below threshold (0.75): {score:.2f}")
                    else:
                        logger.warning(f"[Pipeline] Could not extract score from signal {i+1}")
                else:
                    logger.warning(f"[Pipeline] No 'Launch Likelihood' found in signal {i+1} result")
            
            # Add pipeline summary
            logger.info(f"[Pipeline] Pipeline completed successfully!")
            logger.info(f"[Pipeline] Total signals processed: {len(enriched_signals)}")
            logger.info(f"[Pipeline] High-confidence alerts sent: {len(high_confidence_signals)}")
            
            alert_summary = f"\n**High-Confidence Alerts:** {len(high_confidence_signals)} signals sent to Slack" if high_confidence_signals else "\n**High-Confidence Alerts:** None"
            results.append({
                "type": "text",
                "text": f"🚀 **Stealth Launch Detection Pipeline Complete**\n\n"
                       f"**Query:** {query}\n"
                       f"**URLs Analyzed:** {len(enriched_signals)}\n"
                       f"**Fields Extracted:** {', '.join(target_fields)}\n"
                       f"**Analysis Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{alert_summary}\n"
            })
            
            # Add individual signal results
            logger.info(f"[Pipeline] Adding individual signal results...")
            for i, signal in enumerate(enriched_signals, 1):
                url = urls[i-1] if i-1 < len(urls) else "Unknown URL"
                results.append({
                    "type": "text",
                    "text": f"**Signal {i}:**\n"
                           f"**URL:** {url}\n"
                           f"**Content:** {signal['signal_text'][:200]}...\n"
                           f"**Status:** Processed and scored\n"
                })
            
            # Add scoring results
            logger.info(f"[Pipeline] Adding scoring results...")
            results.extend(scoring_result)
            
            logger.info(f"[Pipeline] Returning {len(results)} result blocks to client")
            return results
            
        except Exception as e:
            logger.error(f"[Pipeline] Pipeline error: {e}")
            logger.error(f"[Pipeline] Error details: {traceback.format_exc()}")
            return [{
                "type": "text",
                "text": f"❌ Pipeline failed: {str(e)}"
            }]
    
    def _init_database(self):
        """Initialize SQLite database and create table if it doesn't exist"""
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            db_path = os.path.join("data", "signals.db")
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Create signals table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL,
                        title TEXT,
                        html_excerpt TEXT,
                        changelog TEXT,
                        pricing TEXT,
                        score REAL,
                        confidence TEXT,
                        reasoning TEXT,
                        created_at TEXT NOT NULL
                    )
                ''')
                
                # Create index on created_at for better query performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_signals_created_at 
                    ON signals(created_at)
                ''')
                
                conn.commit()
                logger.info(f"[DB] Database initialized at {db_path}")
                
        except Exception as e:
            logger.error(f"[DB] Failed to initialize database: {e}")

    def store_signal(self, signal: Dict[str, Any]) -> bool:
        """Store a scored signal in the SQLite database"""
        try:
            db_path = os.path.join("data", "signals.db")
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Insert signal data
                cursor.execute('''
                    INSERT INTO signals (
                        url, title, html_excerpt, changelog, pricing, 
                        score, confidence, reasoning, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal.get("url", ""),
                    signal.get("title", ""),
                    signal.get("html_excerpt", ""),
                    signal.get("changelog", ""),
                    signal.get("pricing", ""),
                    signal.get("score", 0.0),
                    signal.get("confidence", ""),
                    signal.get("reasoning", ""),
                    signal.get("created_at", datetime.now().isoformat())
                ))
                
                conn.commit()
                
                url = signal.get("url", "Unknown")
                score = signal.get("score", 0.0)
                logger.info(f"[DB] Stored signal for {url} with score {score}")
                return True
                
        except Exception as e:
            logger.error(f"[DB] Failed to store signal: {e}")
            return False

    def _extract_urls_from_search_results(self, search_text: str) -> List[str]:
        """Extract URLs from search results text"""
        # Look for URLs in the search results
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, search_text)
        
        # Filter out common non-article URLs
        filtered_urls = []
        for url in urls:
            if any(domain in url for domain in [
                'techcrunch.com', 'theverge.com', 'wired.com', 'arstechnica.com',
                'ycombinator.com', 'betalist.com', 'venturebeat.com', 'engadget.com',
                'gizmodo.com', 'techradar.com', 'zdnet.com', 'cnet.com', 'producthunt.com'
            ]):
                filtered_urls.append(url)
        
        return filtered_urls[:10]  # Limit to 10 URLs max

    async def send_slack_alert(self, title: str, score: float, url: str, fields: Dict[str, str] = None) -> bool:
        """Send Slack alert for high-confidence stealth signals"""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not set, skipping Slack alert")
            return False
        
        try:
            # Format the fields as bullet points
            fields_text = ""
            if fields:
                for key, value in fields.items():
                    if value and value.strip():
                        fields_text += f"• *{key.title()}:* {value}\n"
            
            # Format the Slack message
            message = {
                "text": "🚨 *Stealth Launch Detected*",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 Stealth Launch Detected"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Title:* {title}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Score:* {score:.2f}/1.0"
                            }
                        ]
                    }
                ]
            }
            
            # Add fields section if we have extracted fields
            if fields_text:
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Details:*\n{fields_text}"
                    }
                })
            
            # Add URL section
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🔗 <{url}|View Source>"
                }
            })
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent successfully for: {title}")
                        return True
                    else:
                        logger.error(f"Slack alert failed with status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False

async def main():
    """Main MCP server loop - reads from stdin, writes to stdout"""
    server = MCPStdioServer()
    
    logger.info("Starting MCP stdio server...")
    
    try:
        while True:
            # Read JSON-RPC request from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                response = await server.handle_request(request)
                
                # Send response to stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                continue
                
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
