#!/usr/bin/env python3
"""
Test script for FastAPI server endpoints
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🧪 Testing {description}")
    print(f"   {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict) and "content" in result:
                print(f"   Success: {len(result['content'])} content blocks")
                if result.get("isError"):
                    print(f"   ⚠️  Error in response: {result['content'][0].get('text', 'Unknown error')}")
                else:
                    print(f"   ✅ Response received successfully")
            else:
                print(f"   ✅ Response: {result}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def main():
    print("🚀 Testing Stealth Launch Radar FastAPI Server")
    print("=" * 50)
    
    # Test basic endpoints
    test_endpoint("GET", "/health", description="Health Check")
    test_endpoint("GET", "/tools", description="Tools List")
    test_endpoint("GET", "/", description="Root Endpoint")
    
    # Test tool endpoints
    test_endpoint("POST", "/tools/web_search", 
                 {"query": "stealth AI startup", "num_results": 2}, 
                 "Web Search")
    
    test_endpoint("POST", "/tools/score_signal", 
                 {"signal_text": "We are launching our new AI product in stealth mode", "signal_title": "Test Signal"}, 
                 "Score Signal")
    
    test_endpoint("POST", "/tools/url_extract", 
                 {"url": "https://example.com", "parsing_type": "plain_text"}, 
                 "URL Extract")
    
    test_endpoint("POST", "/tools/search_tech_sites", 
                 {"query": "AI startup", "num_results": 2}, 
                 "Search Tech Sites")
    
    test_endpoint("POST", "/tools/parse_fields", 
                 {"html": "<html><body><h1>Test</h1><p>Pricing: $99/month</p></body></html>", "target_fields": ["pricing"]}, 
                 "Parse Fields")
    
    test_endpoint("POST", "/tools/batch_score_signals", 
                 {"signals": [{"signal_text": "Test signal 1"}, {"signal_text": "Test signal 2"}]}, 
                 "Batch Score Signals")
    
    test_endpoint("POST", "/tools/run_pipeline", 
                 {"query": "stealth startup", "num_results": 1, "target_fields": ["pricing"]}, 
                 "Run Pipeline")
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print(f"📖 API Documentation: {BASE_URL}/docs")
    print(f"🔧 Smithery compatible endpoints ready")

if __name__ == "__main__":
    main()
