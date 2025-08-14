#!/bin/bash
# Test CLI with real credentials
# Set these first:
# export MATTERPORT_API_KEY="your_key"
# export MATTERPORT_API_SECRET="your_secret" 
# export MP_MODEL_ID="your_model_id"

echo "🚀 Testing mp-geo-export CLI..."

# Test 1: Help
echo "📖 Testing help..."
mp-geo-export --help

# Test 2: Export panos as JSON (quiet)
echo "📍 Testing panos export (JSON)..."
mp-geo-export export panos --model-id "$MP_MODEL_ID" --format json --no-pretty | head -3

# Test 3: Export tags as CSV 
echo "🏷️  Testing tags export (CSV)..."
mp-geo-export export tags --model-id "$MP_MODEL_ID" --format csv --out tags.csv --max-rps 2.0 --concurrency 3

if [ -f tags.csv ]; then
    echo "✅ CSV file created:"
    head -3 tags.csv
    rm tags.csv
fi

# Test 4: Test with different resolution
echo "📷 Testing high-res panos..."
mp-geo-export export panos --model-id "$MP_MODEL_ID" --resolution 4k --no-include-skybox --format json | head -2

echo "✅ CLI tests complete!"
