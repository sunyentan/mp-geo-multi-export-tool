## mp-geo-export

Export Matterport model data (panos, tags, notes) with geocoordinates as JSON/CSV.

Why two steps? Matterport GraphQL returns local model coordinates (x,y,z). To obtain real-world latitude/longitude, you must resolve each point via `model.geocoordinates.geoLocationOf(modelLocation: IPoint3D!)`. This tool automates fetching objects, resolving geo, and writing clean outputs.

### Install

- Recommended (CLI):
```
pipx install .
```

- Or library/CLI:
```
pip install .
```

Python 3.10+.

### Credentials & Security

Provide credentials via one of the following, in priority order:

- Keyring: service `mp-geo-export`, username `matterport-basic` (stores `key:secret`).
- Environment variables: `MATTERPORT_API_KEY`, `MATTERPORT_API_SECRET`, `MATTERPORT_API_URL` (optional).
- CLI flags: `--api-key`, `--api-secret`, `--url` (no persistence).
- Interactive prompt if none provided; choose `--save-to-keyring/--no-save-to-keyring` (default save when prompted).

Secrets are never written to disk. Persistence uses OS keyring only. `.env` is supported for non-secret settings; see `.env.example`.

Default API URL: `https://api.matterport.com/api/models/graph`.

### Usage

```
mp-geo-export export panos --model-id <MODEL_ID> --format json > panos.json
mp-geo-export export tags  --model-id <MODEL_ID> --format csv  --out tags.csv
mp-geo-export export panos --model-id <MODEL_ID> --no-include-skybox
mp-geo-export export panos --model-id <MODEL_ID> --resolution 4k --concurrency 12 --max-rps 8
```

Common flags:

- `--model-id TEXT` (required unless `MP_MODEL_ID` set)
- `--out PATH` default `-` (stdout)
- `--format [json|csv]` default `json`
- `--resolution [1k|2k|4k]` (panos)
- `--concurrency INTEGER` default 8
- `--max-rps FLOAT` default 5.0
- `--retries INTEGER` default 3
- `--timeout FLOAT` default 30.0
- `--include-skybox/--no-include-skybox` (panos) default true
- `--pretty/--no-pretty` JSON pretty default true for TTY
- `--csv-headers/--no-csv-headers` default true
- `--api-key --api-secret --url` overrides
- `--save-to-keyring/--no-save-to-keyring` when prompted

CSV headers:

- Panos: `id,lat,long,alt,x,y,z,skybox_0,...,skybox_5`
- Tags: `id,label,lat,long,alt,x,y,z`
- Notes: `id,text,lat,long,alt,x,y,z`

### Programmatic use

```python
from mp_geo_export import export_panos

rows = export_panos("MODEL_ID", include_skybox=True, resolution="2k")
```

### Notes on rate limiting & retries

The client applies simple per-request rate limiting and retry with exponential backoff to avoid hammering the GraphQL endpoint.

### Development

Run tests:
```
pytest -q
```

Type-check:
```
mypy src
```

# mp-geocoord-export
Export geo coordinates of sweeps, tags, etc
