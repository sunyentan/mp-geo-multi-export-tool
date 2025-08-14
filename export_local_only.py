#!/usr/bin/env python3
"""
Modified version that exports local coordinates without geocoding
for models that don't have georeference data.
"""
import os
import json
from mp_geo_export.api import ApiClient
from mp_geo_export.auth import get_auth_header
from mp_geo_export.config import api_url
from mp_geo_export.models import GeoPoint

def export_local_data():
    client = ApiClient(api_url(), get_auth_header())
    model_id = os.getenv("MP_MODEL_ID")
    
    print(f"🚀 Exporting LOCAL data for model: {model_id}")
    
    # Export locations with local coordinates only
    print("\n📍 PANOS & LOCATIONS:")
    locations = client.fetch_locations(model_id, "2k")
    pano_exports = []
    
    for i, loc in enumerate(locations):
        panos = loc.get("panos") or []
        for j, pano in enumerate(panos):
            skybox = pano.get("skybox", {}).get("children", [])
            export = {
                "id": f"{loc['id']}_pano{j+1}",
                "local_coordinates": loc["position"],
                "skybox_images": skybox if len(skybox) == 6 else None,
                "location_id": loc["id"]
            }
            pano_exports.append(export)
    
    print(json.dumps(pano_exports, indent=2))
    
    # Export tags with local coordinates only  
    print("\n🏷️ TAGS:")
    tags = client.fetch_tags(model_id)
    tag_exports = []
    
    for tag in tags:
        export = {
            "id": tag["id"],
            "label": tag.get("label"),
            "local_coordinates": tag["anchorPosition"]
        }
        tag_exports.append(export)
        
    print(json.dumps(tag_exports, indent=2))
    
    print(f"\n✅ Successfully exported {len(pano_exports)} panos and {len(tag_exports)} tags")
    print("📝 Note: This model has no geocoordinate data, but local coordinates work perfectly!")

if __name__ == "__main__":
    export_local_data()
