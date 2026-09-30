# Implementation status and limitations

This is a working local prototype, not the completed production deployment described in the aspirational brief. The following distinctions are material.

| Capability | Status |
|---|---|
| Seven-page connected operations UI, history/monitoring, station tabs, scenario lab | Implemented; browser workflows checked |
| Raw append-only DB rows, ingestion, duplicate/order/future checks | Implemented; database and API tests |
| Heartbeat outages and software offline buffering/replay | Implemented; tests; software emulator only |
| T/P/RH physics representations | Implemented baseline; not instrument-certified |
| Temporal forecast, frozen checks, robust peer trends | Implemented causal baseline |
| Isolation Forest | Trained on synthetic normal data; real artifact |
| Six operational classes, incidents, notes, feedback | Implemented deterministic baseline, incomplete scenario coverage |
| Virtual twin | Temporal baseline with heuristic intervals; full learned ensemble not implemented |
| Corrections | T/RH consensus proposals, audited human review; no raw mutation |
| Reports and benchmark dashboard | Stored data/artifact based; limited export sizes documented |
| Tiny dense autoencoder INT8 | Trained, converted, desktop inference verified; 8,336-byte file |
| C++ edge rules and buffer | Host compiled and tested |
| TFLite Micro board adapter | Source provided; board/toolchain compilation and flashing pending |
| Original satellite/3D map | User will provide later; community northern correction, historical base elsewhere |
| PostgreSQL / Docker Compose | Configuration supplied; check work log for local execution status |
| MQTT bridge | Adapter supplied; real broker/device integration untested |
| Real AWS / IMD datasets | Not supplied, not validated |
| Learned calibrated fusion / conformal uncertainty | Not implemented; no probabilities displayed |
| Long-history seasonal climatology | Not implemented; insufficient history flagged |
| Lag-aware fronts, elevation/correlation-weighted neighbors | Not implemented; simple geographic candidate selection |
| Sequence-model / TinyTimeMixer comparisons, SHAP | Not implemented; no model-selection superiority claim |
| Maintenance forecasting | Transparent health/risk index only; no time-to-failure claim |
| Model drift monitoring and promotion/rollback | Offline v2 comparison gates implemented; automatic drift monitoring/rollback not implemented |
| RBAC / per-device auth / HA / migrations | Not implemented; local API key and process-local controls only |
| Full-scale real-weather stress tests / blinded final benchmark | Pending representative real data and evaluation protocol |

## Scientific limitations

Synthetic station data deliberately simplifies climatic diversity and uses MSL pressure. Sensor error distributions, true extreme weather, snow/ice humidity behavior, changes in cadence, complex mixed faults and site-specific biases need broader validation. Ordinary diurnal behavior can resemble a weather transition; conservative abstention is preferable to unsupported certainty. Drift and sustained-event persistence remain imperfect. Numeric heuristics and expected ranges are not calibrated uncertainty.

The small synthetic evaluation is a development regression fixture. Its numbers must never be advertised as production accuracy. Empty metrics remain unavailable. No physical-board measurements or cryptographic audit claims exist.

## Operational limitations

Run one API worker. A Python process lock does not serialize multiple workers or replicas. SQLite is a local convenience. Per-station histories and neighbor queries are not optimized for a national production network. Requests with a valid shared API key have operator privileges; a key is not RBAC. Demo mode is unauthenticated by default and binds to loopback. Malformed schemas are rejected rather than retained in a raw byte quarantine. Historical packet replay does not rewrite old predictions.

No external notifications, operational weather products, government systems or public website were published. Only local demonstration records were changed during QA.

The expanded archive can be extended from 30 to 90 days of synthetic hourly observations, not the ten-year NOAA archive discussed in the reference video. Additional sites are generated coordinates, not actual registered AWS installations. Continuous simulation is implemented; an external live observation provider is not connected. History aggregation is bounded to 150,000 records per selected station and is not a large-scale analytical warehouse.

The larger benchmark evaluates 12,000 controlled copies of stored archive samples across 500 stations. The rest of the archive is not claimed to be scored. Ground-truth fault labels are injected experimental labels, not human-confirmed field incidents. That archived v1 model was trained at ten-minute cadence; this hourly dataset intentionally exposes its cadence sensitivity. No performance improvements are assumed from volume alone.

- Regional simulation v2 adds deterministic station, latitude/longitude, elevation, diurnal and synoptic variation in T/P/RH. It is illustrative synthetic weather, not observed climatology. Generated sites with unknown elevation in the far north use a synthetic terrain proxy; pressure remains MSL. Existing archive data and original benchmark remain unchanged. Those benchmark metrics do not establish accuracy for this new distribution.
- Versioned simulation histories warm up independently after a generator change to avoid interpreting the synthetic regime switch as a sensor fault. Original raw records, decisions and reviews remain available. Current dashboard readings update after each committed simulation batch; readers can continue seeing the previous committed snapshot during generation.
- Regional-v3 adds station-specific shorter-period fluctuations and measurement noise. The mixed-network demonstration creates controlled weather/fault/outage/ambiguous inputs and runs actual detection; the resulting statuses are illustrative synthetic events, not field observations or new benchmark metrics. Normal-operation scenarios and the normal monitoring stream can subsequently change these states as new observations arrive. Existing immutable archive curves retain their original generator.

- Station Intelligence exposes an investigative Virtual Buddy baseline using existing fresh, trusted T/P/RH peer tendencies and same-version causal history. It is not an independently validated prediction, NWP integration, or replacement for stored diagnosis/twin evidence. Geographic candidate selection is not terrain/correlation weighted. Classical z/MAD statistics and health tiers are uncalibrated diagnostics, not failure probabilities.
- Seven/thirty-day sensor charts include available stored synthetic archive records. Correction markers display actual proposed/approved candidates separately from immutable raw values; rejected candidates are hidden. The station location map uses bundled regional boundaries; it does not contain street tiles. The external OpenStreetMap link requires network access. Distances and scale use a local equirectangular approximation.
- Regional-v4 varies daily shapes using reproducible smooth random cloud, moisture, pressure and regional air-mass components. It is synthetic illustrative variation, not measured meteorology. Existing archive/older versions are preserved, so long-range history may still show earlier generator patterns. Generator changes start a fresh causal warm-up; benchmark artifacts are not claims about this new distribution.
- Analytics uses a complete rolling 24-hour observation window with 10-minute count buckets. Equal bar heights can legitimately reflect a fixed number of stations reporting at a fixed cadence; status composition is determined by actual recorded decisions. Missing communications appear in current network status, not as fabricated observation rows. RH expected bands are visually limited to 0–100%; actual out-of-range observations remain visible.

- Street roads are real OpenStreetMap way geometry requested from Overpass for the current close-zoom viewport (>=45× national zoom), rendered directly over the original terrain. Road names are limited to 18 distinct names per request. Requests wait for camera movement to stop, use a bounded 16-area memory cache and a 30-second failure cooldown. Internet/service availability and OSM coverage determine detail; no replacement raster basemap or fabricated roads. Public Overpass is best-effort; production traffic needs a suitable geographic data service. No telemetry is sent, only geographic query bounds.

- The active historical demo edition regenerates legacy synthetic timestamps with regional-v4, preserving all original raw records separately. Historical edition samples are stored, unscored and never supplied to online inference; earlier correction candidates/decisions remain available with Original records or Online processed. The Data view and sensor charts use the current edition by default after complete activation. Long-range averages smooth hourly fluctuations naturally; operational count charts and benchmark metrics still use actual stored decisions, not fabricated variation.

- Active hybrid-regional-2 is evaluated separately on 4,032 synthetic samples. Fault recall improves to 85.8% on its paired cohort, while weather recall remains 9.7%. Retrained IF greatly reduces normal novelty flags but also reduces IF-only fault novelty recall; the operational improvement comes from the combined pipeline, especially cadence-aware flatline checks. These development results share a generator family with training, omit supported BOTH_COMPLEX cases and do not establish real-world generalization. See [ML improvement report](ML_IMPROVEMENT.md). Stored v1 decisions and archive benchmarks are retained.
