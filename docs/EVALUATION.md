# Evaluation

`make evaluate` writes `ml/artifacts/evaluation.json` and the observation-level `predictions.json`. The dashboard reads those files through the API. It never substitutes the reference screenshots' scores.

Current fixture: 504 labeled stress observations from three deterministic seeds, seven scenarios and station indices held out from fitting. Each case has a causal warm-up. Dates are later than the synthetic training range. Fault labels are held in the evaluation harness, never inserted into detector packets. Scenarios cover normal, spike, drift, freeze, regional weather, ambiguous local change and invalid RH.

Reported results include fault precision/recall/F1, supported-class macro F1, per-class support and scores, confusion matrix, normal false-alert rate, weather-as-sensor-fault rate, abstentions and decision-only host latency percentiles. The live telemetry page separately reports end-to-end processing latency from stored observations, including database work.

Important boundaries:

- These are synthetic development regression results, not a blinded final test or real AWS validation. The implementation was improved after reviewing this fixture.
- `BOTH_COMPLEX` has no positive test support in the benchmark; its zero-valued metric must not be interpreted as measured performance for that class.
- Sustained weather can return to NORMAL after the local baseline adapts. Thus observation-level weather recall is weaker than onset detection; no event-level detection-delay claim is currently made.
- No calibration probabilities are produced, so Brier/ECE are unavailable rather than zero.
- No field hardware exists in this task. MCU memory/latency/power stay unavailable. Edge file size and desktop INT8 inference timings are measured separately.
- Full ablations, candidate-model comparisons, forecast/correction interval calibration, real extreme-weather stress tests, load targets and independent final holdout are future work.

`make test` additionally checks schemas, physics units, future leakage, elapsed-time rates, unavailable evidence, normal/spike/weather behavior, faulty-peer robustness, pressure-reference-safe tendencies, raw immutability, delivery idempotency, atomic batch rollback, late/future packet exclusion, heartbeat outages, edge buffering/replay, health recovery, API/report roundtrips and correction review.

## Larger stored-archive evaluation

`make expand-dataset` adds stations up to 500 and extends the synthetic hourly archive to 90 days (1,080,000 raw archive rows). Pause the simulated stream and stop the API during this offline bulk import. The script commits per station and safely resumes; it does not replace any raw rows. `make evaluate-archive` then evaluates the existing fixed model on the last 72 stored hourly observations for each station: 48 causal warm-up records followed by 24 labeled test copies. This yields 12,000 measured predictions across 500 stations, not a claim that all one million archive rows were scored.

Seven scenarios are assigned cyclically by station ID: normal, temperature spike, gradual temperature drift, frozen RH, regional weather, ambiguous local change and invalid RH. The evaluator preserves source observation IDs and original T/P/RH alongside controlled test-copy inputs. Truth labels stay outside the model input. Five closest sites supply a clean trusted-reference cohort; weather perturbations are applied coherently to that cohort. These controlled reference assumptions do not establish robustness to arbitrary real network faults.

The model is not retrained and thresholds are not tuned on these results. Evaluation timestamps occur after the January synthetic training period, but the same family of generators is used; this is not independent climate-distribution validation. Hourly archive cadence differs from the original ten-minute training and frozen-sensor window, making this a useful cadence stress test. Observation accuracy and fault recall may drop. Do not hide these failures or compare the two benchmarks as if their distributions were identical.

The new summary is `ml/artifacts/evaluation_large.json`; the original 504-row artifact is retained. The API and Analytics prefer the larger summary when available. Full labeled predictions live in the separate `benchmark_predictions` database table and are browsable under **Data → Dataset & ML results**, including a misclassified-only filter. Those predictions do not rewrite operational incidents, station states, raw measurements or correction reviews.

### Measured archive run, 22 September 2026

500 stations; 12,000 labeled predictions; 1,080,000 archive observations available. Hybrid fault precision 100.00%, recall 75.07%, F1 85.76%; normal false-alert rate 0.00%. Exact scenario accuracy: normal 100.00%, spike 100.00%, drift 77.26%, freeze 22.65%, weather 12.62%, ambiguous 0.00%, invalid 100.00%.

Isolation Forest alone: novelty precision 99.13%, recall 46.68%, F1 63.47%. This is normal-versus-perturbed novelty detection, not fault-versus-weather classification. The model misses many hourly perturbations. The hybrid frozen, weather and ambiguous-class results expose important limitations; they are displayed without tuning to this test. More synthetic volume did not make the model universally reliable.
