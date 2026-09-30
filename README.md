# SkyGuard

Automatic Weather Station intelligence and data trust platform for the supplied SIH26073 brief. All meteorological intelligence uses **temperature, atmospheric pressure and relative humidity only**. External weather forecasts, NWP, wind and rain are excluded.

This repository contains a working, local end-to-end prototype: React/TypeScript operations UI, FastAPI service, durable observations and operator reviews, causal diagnostic baseline, reproducible synthetic evaluation, and a trained INT8 edge autoencoder. It is **not yet a field-validated production system**. See [implementation status and limitations](docs/LIMITATIONS.md).

## Run locally

Requires Node 22+ and [uv](https://docs.astral.sh/uv/). Python 3.12 is installed by uv when needed.

```sh
make setup
make dev
```

- Dashboard: http://127.0.0.1:5173
- Backend and API documentation: http://127.0.0.1:8010/docs
- Local persistence: `data/skyguard.db` (SQLite)
- Simulation startup seeds the original 54 stations, then performs an additive expansion to 198 synthetic stations with a 30-day hourly archive (the larger local dataset is reproducible with `make expand-dataset`). Existing databases are upgraded once without deleting observations. First startup can take a few minutes. No real IMD connection is implied.
- Stop with Ctrl+C. Data survives restarts. Never delete or reset the database merely to restart the demo.

Alternatively run `make api` and `make ui` in separate terminals. Port 8010 is intentional; port 8000 was already occupied on the development machine.

## Container deployment

```sh
docker compose up --build
```

Dashboard: http://127.0.0.1:8080. This configuration uses PostgreSQL and a persistent named volume. It binds the frontend to loopback by default. Docker configuration is included; consult the work log for whether it was tested on the current machine.

## What works

- Overview with geographic 3D station map; station filters/search and detail pages.
- Data workspace: date-range history, station comparison, aggregates, paginated ledger and CSV export.
- Monitoring console: rolling observations, station filter, freshness, refresh controls and continuous simulation start/pause. See [history and monitoring](docs/HISTORY_MONITORING.md).
- T/P/RH time series, physics transforms, virtual-twin baseline, detector evidence and missing-source indicators.
- Immutable raw rows, idempotent delivery, late/future/duplicate packet detection and heartbeat outages.
- Six operational classes; root causes stored separately; evidence strength explicitly uncalibrated.
- Incidents, reviewer notes, feedback labels, review states and audit records.
- Separate correction candidates requiring operator approval, with unchanged raw values.
- Deterministic scenario lab and software edge disconnect/buffer/reconnect demonstration.
- Analytics from stored decisions and evaluation files; JSON/CSV reports.
- Synthetic Isolation Forest training and evaluation; trained 36→32→8→32→36 INT8 autoencoder; portable C++ edge screening/ring buffer and TFLM integration adapter.

## Reproduce artifacts and checks

```sh
make train          # train synthetic Isolation Forest and prepare edge windows
make evaluate       # original 504-sample synthetic regression
make expand-dataset # API stopped, stream paused: 500 sites / 90-day archive
make evaluate-archive # evaluate 12,000 labeled copies of stored observations
make train-edge     # train and quantize TensorFlow model; isolated extra dependencies
make benchmark-edge # host CPU measurements only
make test           # Python/API/science/persistence + portable C++ checks
make build          # TypeScript + Vite production build
make generate-data  # export deterministic synthetic CSV
make replay-demo    # invoke scenario against a running local API
```

Model artifacts are in `ml/artifacts/` and `edge/models/`. Metrics are measured, not reference-image placeholders. Synthetic benchmarks cannot establish real-world performance. Changing implementation after viewing these benchmarks makes them development regression results, not a blinded final evaluation.

## Live ingestion

Use a separate database for physical stations. Set `SKYGUARD_MODE=live` and configure `SKYGUARD_API_KEY` before startup. Register station metadata with `POST /api/v1/stations`, then send observations to `POST /api/v1/observations` or `/observations/batch`. The UI can accept the API key for the current session; it is not saved to browser storage. Live mode disables the simulator.

CSV uses the same schema and maximum 1,000-row atomic batch. The optional `scripts/mqtt_bridge.py` adapter requires `paho-mqtt`, an explicitly configured broker and station registration. It forwards telemetry through the validated HTTP API; it has not been tested against a real broker. There is no IMD credential or external weather feed in this repository.

## Continue development

Read [WORK_LOG.md](WORK_LOG.md) first. It records decisions, checks, running-service details, and next work. [AGENTS.md](AGENTS.md) directs future coding sessions to keep the log current. Both source briefs are preserved in `references/`; the second brief supersedes the first wherever T/P/RH-only constraints conflict.

The user's existing India map project will be supplied later. `frontend/src/Map.tsx` is the replaceable integration boundary. The temporary map uses historical geographic polygons, not a geographic authority or meteorological input. Attribution and data limitations are in [ASSETS.md](docs/ASSETS.md).

## Station intelligence and reference features

Use **Stations → Station cards** to search/filter health tiers and open reports. The **Intelligence** report tab shows telemetry completeness, causal T/P/RH statistics, nearby-station Virtual Buddy context and recorded detection explanations. **Sensors** supports individual parameters and 7/30-day ranges with stored correction candidates. The station location panel uses locally served regional boundaries and nearby station dots; street detail opens in OpenStreetMap externally. See [reference comparison](docs/REFERENCE_COMPARISON.md) for provenance and boundaries.

If another local service occupies port 8010, run the API on an unused port and start the UI with `SKYGUARD_API_TARGET=http://127.0.0.1:8011 npm run dev` from `frontend`. The default remains 8010.

To rebuild varied historical demonstration data, pause continuous simulation and run `uv run python scripts/refresh_archive.py`. It appends a resumable versioned edition across all existing synthetic timestamps, then activates it only when complete. Budget roughly 1 GB of free disk space. Original records remain selectable in Data; regenerated historical samples are unscored and excluded from live ML history.

## Regional ML v2

The active server pipeline uses the regional-v2 Isolation Forest and cadence-aware frozen-sensor checks. Analytics shows the paired 4,032-sample synthetic comparison; Dataset & ML results retains the original 12,000-sample archive benchmark. New observations use v2; stored diagnoses are unchanged. See [ML improvement report](docs/ML_IMPROVEMENT.md) for measured gains, tradeoffs and reproduction commands.
