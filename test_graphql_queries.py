#!/usr/bin/env python3
"""
Test individual GraphQL queries to debug API responses.
"""
import os
import json
import base64
import requests
from mp_geo_export.queries import GET_SWEEPS, GET_TAGS, GET_NOTES, GET_GEO

def test_query(query_name, query, variables, api_key, api_secret):
    """Test a single GraphQL query."""
    url = "https://api.matterport.com/api/models/graph"
    
    # Create auth header
    auth_token = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    print(f"\n🔍 Testing {query_name}")
    print(f"Variables: {variables}")
    
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if "errors" in data:
                print(f"❌ GraphQL Errors: {data['errors']}")
            else:
                print(f"✅ Success! Data keys: {list(data.get('data', {}).keys())}")
                # Print first level of data structure
                for key, value in data.get('data', {}).items():
                    if isinstance(value, dict):
                        print(f"   {key}: {list(value.keys())}")
                    elif isinstance(value, list):
                        print(f"   {key}: [{len(value)} items]")
                    else:
                        print(f"   {key}: {type(value).__name__}")
        else:
            print(f"❌ HTTP Error: {resp.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def main():
    api_key = os.getenv("MATTERPORT_API_KEY")
    api_secret = os.getenv("MATTERPORT_API_SECRET") 
    model_id = os.getenv("MP_MODEL_ID")
    
    if not all([api_key, api_secret, model_id]):
        print("❌ Set MATTERPORT_API_KEY, MATTERPORT_API_SECRET, MP_MODEL_ID")
        return
        
    print(f"🚀 Testing GraphQL queries for model: {model_id}")
    
    # Test each query type
    test_query("GET_SWEEPS", GET_SWEEPS, {"modelId": model_id, "resolution": "2k"}, api_key, api_secret)
    test_query("GET_TAGS", GET_TAGS, {"modelId": model_id}, api_key, api_secret)  
    test_query("GET_NOTES", GET_NOTES, {"modelId": model_id}, api_key, api_secret)
    
    # Test geocoding with a sample point
    sample_point = {"x": 0.0, "y": 0.0, "z": 0.0}
    test_query("GET_GEO", GET_GEO, {"modelId": model_id, "point": sample_point}, api_key, api_secret)

if __name__ == "__main__":
    main()
