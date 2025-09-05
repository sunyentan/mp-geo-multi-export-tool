# mp-geo-export

A Python CLI tool and SDK for exporting Matterport 3D model data (sweeps/panoramas, tags, notes) with real-world geocoordinates as JSON or GeoJSON.

## What This Tool Does

Matterport's GraphQL API returns 3D model coordinates in local space (x,y,z). To get real-world latitude/longitude coordinates, you need to resolve each point through their `model.geocoordinates.geoLocationOf()` endpoint. This tool automates the entire process:

1. **Fetches** all objects (sweeps, tags, notes) from a Matterport model
2. **Resolves** local 3D coordinates to real-world lat/lng coordinates
3. **Exports** clean, structured data in JSON or GeoJSON format

## Quick Start

### Installation

```bash
# Recommended: Install globally with pipx
pipx install .

# Or install as a regular package
pip install .
```

**Requirements**: Python 3.10+

### First Use Setup

1. **Get your Matterport API credentials**:
   - Go to [Matterport Developer Portal](https://matterport.com/developers)
   - Create an app and get your API key and secret

2. **Run your first export**:
   ```bash
   # Export all sweeps/panoramas from a model
   mp-geo-export export sweeps --model-id YOUR_MODEL_ID --format geojson > sweeps.geojson
   
   # Export all tags
   mp-geo-export export tags --model-id YOUR_MODEL_ID --format json > tags.json
   
   # Export all notes
   mp-geo-export export notes --model-id YOUR_MODEL_ID --format geojson > notes.geojson
   ```

## Complete Usage Examples

### Export Sweeps/Panoramas
```bash
# Basic export to stdout
mp-geo-export export sweeps --model-id YOUR_MODEL_ID

# Export to file with GeoJSON format
mp-geo-export export sweeps --model-id YOUR_MODEL_ID --format geojson --out sweeps.geojson

# Include skybox images (6-sided panorama data)
mp-geo-export export sweeps --model-id YOUR_MODEL_ID --include-skybox --format geojson

# High-performance export with custom concurrency
mp-geo-export export sweeps --model-id YOUR_MODEL_ID --concurrency 16 --max-rps 10
```

### Export Tags
```bash
# Export all tags to GeoJSON
mp-geo-export export tags --model-id YOUR_MODEL_ID --format geojson --out tags.geojson

# Export tags to JSON with pretty formatting
mp-geo-export export tags --model-id YOUR_MODEL_ID --format json --pretty
```

### Export Notes
```bash
# Export all notes to GeoJSON
mp-geo-export export notes --model-id YOUR_MODEL_ID --format geojson --out notes.geojson
```

## Command Line Options

### Required
- `--model-id TEXT` - Matterport model ID (or set `MP_MODEL_ID` environment variable)

### Output Options
- `--out PATH` - Output file path (default: stdout)
- `--format [json|geojson]` - Output format (default: json)
- `--pretty/--no-pretty` - Pretty-print output (default: auto-detected for TTY)

### Sweep-specific Options
- `--include-skybox/--no-include-skybox` - Include 6-sided skybox panorama data (default: false)

### Performance Tuning
- `--concurrency INTEGER` - Number of concurrent geocoding requests (default: 8)
- `--max-rps FLOAT` - Maximum requests per second (default: 5.0)
- `--retries INTEGER` - Retry attempts for failed requests (default: 3)
- `--timeout FLOAT` - Request timeout in seconds (default: 30.0)

### Authentication
- `--api-key TEXT` - Matterport API key
- `--api-secret TEXT` - Matterport API secret
- `--url TEXT` - Custom API URL (default: https://api.matterport.com/api/models/graph)
- `--save-to-keyring/--no-save-to-keyring` - Save credentials to OS keyring (default: true when prompted)

## Authentication & Security

The tool supports multiple ways to provide your Matterport API credentials:

### 1. OS Keyring (Recommended)
Credentials are securely stored in your OS keyring and automatically retrieved:
```bash
# First time: you'll be prompted to enter credentials
mp-geo-export export sweeps --model-id YOUR_MODEL_ID

# Subsequent runs: credentials are automatically loaded
mp-geo-export export sweeps --model-id YOUR_MODEL_ID
```

### 2. Environment Variables
```bash
export MATTERPORT_API_KEY="your_api_key"
export MATTERPORT_API_SECRET="your_api_secret"

mp-geo-export export sweeps --model-id YOUR_MODEL_ID
```

### 3. Command Line Flags
```bash
mp-geo-export export sweeps --model-id YOUR_MODEL_ID \
  --api-key "your_api_key" \
  --api-secret "your_api_secret"
```

### 4. Interactive Prompt
If no credentials are provided, you'll be prompted to enter them interactively.

**Security Note**: Credentials are never written to disk. The OS keyring uses your system's secure credential storage.

## Output Formats

### JSON Format
Standard JSON array with full object data:
```json
[
  {
    "id": "location_1_pano1",
    "local": {"x": 10.5, "y": 2.1, "z": -5.2},
    "geo": {"lat": 37.7749, "lng": -122.4194},
    "skyboxImages": null
  }
]
```

### GeoJSON Format
Standard geographic data format with Point geometries:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-122.4194, 37.7749]
      },
      "properties": {
        "id": "location_1_pano1",
        "local_x": 10.5,
        "local_y": 2.1,
        "local_z": -5.2
      }
    }
  ]
}
```

## Programmatic Usage

### Python SDK
```python
from mp_geo_export import export_sweeps, export_tags, export_notes

# Export sweeps with skybox data
sweeps = export_sweeps(
    "MODEL_ID", 
    include_skybox=True, 
    resolution="2k",
    concurrency=16
)

# Export tags
tags = export_tags("MODEL_ID")

# Export notes
notes = export_notes("MODEL_ID")

# Access the data
for sweep in sweeps:
    print(f"Sweep {sweep.id}: {sweep.geo.lat}, {sweep.geo.lng}")
```

### Advanced Configuration
```python
from mp_geo_export import export_sweeps

# Custom API client configuration
sweeps = export_sweeps(
    "MODEL_ID",
    api_key="your_key",
    api_secret="your_secret",
    url="https://custom-api.example.com",
    concurrency=20,
    max_rps=15.0,
    retries=5,
    timeout=60.0
)
```

## Rate Limiting & Performance

The tool includes built-in rate limiting and retry logic:
- **Rate Limiting**: Configurable requests per second (default: 5 RPS)
- **Concurrency**: Parallel geocoding requests (default: 8 concurrent)
- **Retries**: Exponential backoff for failed requests (default: 3 attempts)
- **Progress Bars**: Visual feedback for long-running operations

## Development

### Setup Development Environment
```bash
# Clone and install in development mode
git clone https://github.com/sunyentan/mp-geocoord-export.git
cd mp-geocoord-export
pip install -e .

# Install development dependencies
pip install pytest mypy
```

### Run Tests
```bash
pytest -q
```

### Type Checking
```bash
mypy src
```

## Troubleshooting

### Common Issues

1. **"Model not found" error**
   - Verify your model ID is correct
   - Ensure your API credentials have access to the model

2. **Rate limiting errors**
   - Reduce `--concurrency` and `--max-rps` values
   - The tool automatically retries with exponential backoff

3. **Authentication errors**
   - Check your API key and secret
   - Try clearing stored credentials: `keyring delete mp-geo-export matterport-basic`

4. **Large models timing out**
   - Increase `--timeout` value
   - Use higher `--concurrency` for faster processing

### Getting Help
- Check the [Matterport API documentation](https://matterport.com/developers)
- Review the command help: `mp-geo-export --help`
- Check specific command help: `mp-geo-export export sweeps --help`

