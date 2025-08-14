#!/usr/bin/env python3
"""
Script to test mp-geo-export with real Matterport API credentials.

Usage:
    python3 test_real_api.py

Set these environment variables:
    MATTERPORT_API_KEY=your_api_key
    MATTERPORT_API_SECRET=your_api_secret
    MP_MODEL_ID=your_model_id
"""
import os
import sys
from mp_geo_export import export_panos, export_tags, export_notes

def test_library_api():
    """Test the library API directly."""
    model_id = os.getenv("MP_MODEL_ID")
    if not model_id:
        print("❌ MP_MODEL_ID environment variable not set")
        return False
        
    api_key = os.getenv("MATTERPORT_API_KEY") 
    api_secret = os.getenv("MATTERPORT_API_SECRET")
    if not (api_key and api_secret):
        print("❌ MATTERPORT_API_KEY and MATTERPORT_API_SECRET must be set")
        return False
    
    print(f"🔍 Testing model: {model_id}")
    print(f"🔑 Using API key: {api_key[:8]}...")
    
    try:
        print("\n📍 Fetching panos...")
        panos = export_panos(
            model_id, 
            include_skybox=True, 
            resolution="2k",
            api_key=api_key,
            api_secret=api_secret,
            concurrency=3,
            max_rps=2.0
        )
        print(f"✅ Found {len(panos)} panos")
        if panos:
            print(f"   Sample: {panos[0].id} at ({panos[0].geo.lat}, {panos[0].geo.long})")
            
        print("\n🏷️  Fetching tags...")
        tags = export_tags(model_id, api_key=api_key, api_secret=api_secret)
        print(f"✅ Found {len(tags)} tags")
        if tags:
            print(f"   Sample: {tags[0].id} - '{tags[0].label}' at ({tags[0].geo.lat}, {tags[0].geo.long})")
            
        print("\n📝 Fetching notes...")  
        notes = export_notes(model_id, api_key=api_key, api_secret=api_secret)
        print(f"✅ Found {len(notes)} notes")
        if notes:
            print(f"   Sample: {notes[0].id} - '{notes[0].text}' at ({notes[0].geo.lat}, {notes[0].geo.long})")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing mp-geo-export with real API...")
    success = test_library_api()
    sys.exit(0 if success else 1)
