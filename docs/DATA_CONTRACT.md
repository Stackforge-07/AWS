# Data contract

Only these meteorological values are accepted: `temperature_c`, `pressure_hpa`, `relative_humidity_pct`. Unknown fields, including wind or rainfall, are rejected. All measurements must be finite. Timestamps require a timezone and are normalized to UTC.

```json
{
  "observation_id": "station-001-seq-42",
  "station_id": "station-001",
  "timestamp_utc": "2026-09-21T17:00:00Z",
  "temperature_c": 29.2,
  "pressure_hpa": 1003.6,
  "relative_humidity_pct": 61.4,
  "sequence_number": 42,
  "source": "rest",
  "edge_state": "EDGE_NORMAL",
  "edge_anomaly_score": 0.012,
  "edge_model_version": "edgeguard-int8-synthetic-1"
}
```

Optional metadata is operational, not an additional meteorological predictor. Coordinates select potential neighboring stations and place markers; no weather service is queried. Pressure reference is required in station metadata (`station` or `MSL`). The simulator uses MSL consistently. Spatial pressure comparisons use changes over time rather than pooling absolute pressure across elevation.

Register a station using `POST /api/v1/stations`. IDs contain letters, digits, hyphens or underscores. The OpenAPI page `/docs` documents current routes. Batch ingestion is atomic, limited to 1,000 observations; CSV has the same schema and a 2 MB body limit. Stable observation IDs make redelivery idempotent. A reused ID with different measurements is rejected with 409.

Raw values outside guardrails are retained and flagged. NaN, infinity, missing required fields and malformed schemas are rejected before storage, so no claim is made of archiving arbitrary malformed network bodies.
