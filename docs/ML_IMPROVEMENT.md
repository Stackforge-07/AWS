# Regional ML v2 — 25 September 2026

The active server uses `hybrid-regional-2` with `if-regional-2`. The UI design is unchanged. New inferences use v2; raw observations, historical decisions, correction reviews and the original model artifacts are preserved. The simulation remains paused.

## Measured comparison

Both pipelines were evaluated on the same 4,032 synthetic observations, using their own causal histories. These are development results, not field accuracy.

| Metric | Frozen v1 baseline | Active v2 |
|---|---:|---:|
| Fault recall (sensor + data faults) | 77.47% | 85.76% |
| Fault precision | 100% | 100% |
| Macro F1 (six classes, including unsupported class) | 0.5931 | 0.6139 |
| Normal observations incorrectly called faults | 0% | 0% |
| Weather observations incorrectly called faults | 0% | 0% |
| Normal class recall | 97.92% | 97.92% |
| Genuine-weather class recall | 9.72% | 9.72% |
| IF-only normal novelty rate | 31.60% | 0.35% |
| IF-only fault novelty recall | 70.36% | 36.33% |

The Isolation Forest becomes more conservative: fewer normal novelty flags, but reduced standalone fault sensitivity. The combined pipeline improves chiefly through cadence-aware frozen-sensor detection. Novelty is evidence, not a fault probability. The additional novelty rule can request manual review; it cannot approve a correction.

## Training and evaluation

- Isolation Forest: 160 trees, 256 maximum samples per tree, seed 4811. Six runtime features: per-minute T/P/RH rates and causal normalized forecast residuals.
- Training: 6,912 regional-v4 synthetic normal feature rows from 24 station identities; threshold validation: 1,728 rows from six separate identities. January 2026, 10-minute and hourly cadences. Validation median and 99.5th-percentile novelty scores define the score mapping; this is not probability calibration.
- Evaluation: 24 unseen synthetic identities (indices 407–430), seed 55027, timestamps from October 1, 2026. Dates are simulated, not collected observations. Seven scenarios: normal, spike, drift, freeze, weather, ambiguous and invalid data. Each station/scenario has 36 warm-up and 24 scored steps. Twelve identities use each cadence.
- Labels never enter inference features or histories. Both models retain their own past-only trust decisions. Neighbors are related synthetic series, not independent field measurements.
- Promotion gates require improved fault recall and macro F1, fault precision >=99%, normal recall loss <=3 percentage points, weather-to-fault rate <=0.5%, and no increase in normal-to-fault errors. All passed. Artifact and source hashes are recorded and checked.
- Broader weather-persistence candidates were rejected because they misclassified ordinary trends as weather. Their summary reports are retained. Final v2 keeps the conservative original weather rule; no service-history classification workaround remains.

## Limits and UI provenance

Weather discrimination remains weak. There are no supported BOTH_COMPLEX examples in this cohort. Training and evaluation share a synthetic generator family, and the implementation was refined using development experiments; this is not a blinded independent benchmark. No real AWS, IMD or physical-board validation is claimed. Cadence adaptation is tested for regular ten-minute/hourly histories, not every irregular outage pattern.

Analytics displays this 4,032-sample comparison and its baseline. Dataset & ML results retains the separate 12,000-sample v1 archive benchmark and its prediction ledger; its 75.1% recall cannot be compared directly with the new cohort's 85.8%. Existing network status and processing latency still reflect stored historical decisions until fresh observations arrive.

## Reproduce

From the repository root:

```sh
uv run python ml/improve_model.py
uv run python ml/promote_model.py
uv run pytest backend/tests -q
cd frontend
npm run build
```

The training script writes candidate artifacts without accessing the live database. The promotion script validates metrics and checksums before marking the evaluation for display. Restart the API to load regenerated weights. The code selects the v2 artifact; this script is an evaluation gate, not a production deployment or automatic rollback system. The original artifacts remain in `ml/artifacts/` for comparison.

## Verification

53 backend tests pass, including hourly freeze detection and guarding normal trends against unsupported weather promotion. TypeScript/Vite production build passes with the existing bundle-size warning. Running API returns v2 metrics (4,032 samples), while legacy metrics and Dataset return the original 12,000 samples. Browser verified Analytics shows 85.8% recall, version and paired comparison. No raw observations were rewritten or rescored.
