#!/usr/bin/env python3
import requests
import base64
import json

# Test locations query without resolution parameter
api_key = "8fcd232321a23de8"
api_secret = "cd9f264695dd4b2adfab2c8b44454451"
model_id = "4qwFcHwxZmr"

auth_token = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
headers = {"Authorization": f"Basic {auth_token}", "Content-Type": "application/json"}

# Test simpler sweeps query without resolution
query = """
query getSweeps($modelId: ID!) {
  model(id: $modelId) {
    locations {
      id
      position { x y z }
      panos {
        skybox { children }
      }
    }
  }
}
"""

resp = requests.post("https://api.matterport.com/api/models/graph", 
                     json={"query": query, "variables": {"modelId": model_id}}, 
                     headers=headers)
print("Locations response:")
data = resp.json()
if "errors" in data:
    print("❌ Errors:", data["errors"])
else:
    print("✅ Success!")
    locations = data["data"]["model"]["locations"]
    print(f"Found {len(locations)} locations")
    if locations:
        loc = locations[0]
        print(f"  Location {loc['id']}: position {loc['position']}")
        if "panos" in loc and loc["panos"]:
            print(f"  Has {len(loc['panos'])} panos")
            pano = loc["panos"][0]
            if pano.get("skybox", {}).get("children"):
                print(f"  Skybox URLs: {len(pano['skybox']['children'])} images")
                print(f"  First image URL: {pano['skybox']['children'][0]}")
