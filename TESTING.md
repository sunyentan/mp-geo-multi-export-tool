# Testing MP-Geo-Export

## ✅ **Tests Already Passed**

1. **Unit Tests**: `python3 -m pytest -v` (7 tests passing)
2. **Type Checking**: `python3 -m mypy src --ignore-missing-imports` (clean)
3. **CLI Structure**: Help commands work correctly
4. **Library Import**: All functions and models importable
5. **Data Models**: Pydantic models serialize correctly
6. **CSV/JSON Output**: File writing works

## 🔧 **Testing with Real API**

### Option 1: Environment Variables
```bash
export MATTERPORT_API_KEY="your_api_key"
export MATTERPORT_API_SECRET="your_api_secret"
export MP_MODEL_ID="your_model_id"

mp-geo-export export panos --format json --pretty
```

### Option 2: CLI Flags
```bash
mp-geo-export export panos \
  --model-id "your_model_id" \
  --api-key "your_api_key" \
  --api-secret "your_api_secret" \
  --format json \
  --out panos.json
```

### Option 3: Interactive (Keyring)
```bash
mp-geo-export export panos --model-id "your_model_id"
# Will prompt for credentials and save to keyring
```

### Option 4: Library Usage
```python
from mp_geo_export import export_panos

panos = export_panos(
    "your_model_id",
    api_key="your_api_key",
    api_secret="your_api_secret",
    include_skybox=True,
    resolution="2k"
)
print(f"Exported {len(panos)} panos")
```

## 🧪 **Test Different Scenarios**

### Test All Export Types
```bash
# Panos with skybox
mp-geo-export export panos -m MODEL_ID --format csv --out panos.csv

# Tags
mp-geo-export export tags -m MODEL_ID --format json --out tags.json

# Notes
mp-geo-export export notes -m MODEL_ID --format csv --out notes.csv
```

### Test Performance Options
```bash
# High concurrency
mp-geo-export export panos -m MODEL_ID --concurrency 16 --max-rps 10

# Conservative settings
mp-geo-export export panos -m MODEL_ID --concurrency 2 --max-rps 1 --retries 5
```

### Test Output Options
```bash
# Pretty JSON to stdout
mp-geo-export export panos -m MODEL_ID --format json --pretty

# Minimal JSON
mp-geo-export export panos -m MODEL_ID --format json --no-pretty

# CSV without headers
mp-geo-export export panos -m MODEL_ID --format csv --no-csv-headers

# No skybox images
mp-geo-export export panos -m MODEL_ID --no-include-skybox
```

## 🛠 **Troubleshooting**

### Check Package Installation
```bash
pip show mp-geo-export
which mp-geo-export
```

### Test Network Connectivity
```bash
# Test API URL
curl -X POST https://api.matterport.com/api/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { __typename }"}'
```

### Enable Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from mp_geo_export import export_panos
# Now see detailed HTTP requests
```

### Common Error Solutions

1. **"Invalid credentials"**: Check API key/secret format
2. **"Model not found"**: Verify model ID is correct
3. **"Rate limited"**: Reduce `--max-rps` value
4. **"Timeout"**: Increase `--timeout` value
5. **"No geolocation"**: Some models don't have geocoordinate data

## 📊 **Expected Output Formats**

### JSON (Panos)
```json
[
  {
    "id": "location123_pano1",
    "local": {"x": 1.5, "y": 2.0, "z": 3.0},
    "geo": {"lat": 37.7749, "long": -122.4194, "alt": 15.0},
    "skyboxImages": ["url1", "url2", "url3", "url4", "url5", "url6"]
  }
]
```

### CSV (Tags)
```csv
id,label,lat,long,alt,x,y,z
tag123,Kitchen,37.7749,-122.4194,15.0,1.5,2.0,3.0
tag124,Living Room,37.7750,-122.4195,15.1,2.5,3.0,4.0
```

## 🚀 **Performance Expectations**

- **Small models** (< 50 points): ~5-10 seconds
- **Medium models** (50-200 points): ~15-30 seconds  
- **Large models** (200+ points): ~1-5 minutes

Adjust `--concurrency` and `--max-rps` based on your API limits.
