# Decision policy

Implemented operational states: NORMAL, GENUINE_WEATHER, SENSOR_FAULT, DATA_COMMS_ISSUE, BOTH_COMPLEX, UNKNOWN_REVIEW. Root cause is separate.

1. Integrity problems and invalid-value safeguards take precedence.
2. A sustained exactly frozen variable produces sensor-fault evidence.
3. Coherent regional T/P/RH changes supported by fresh trusted peers may be marked genuine weather.
4. Isolated strong temporal or spatial-trend disagreement supports a sensor fault; rapid changes are spikes, sustained divergence is gradual drift in this baseline.
5. Ambiguous local deviations or insufficient history return UNKNOWN_REVIEW.
6. Fault-plus-weather combinations can return BOTH_COMPLEX, but mixed-event coverage is limited and is not independently validated.

The operational stage progresses through SUSPICIOUS, VERIFYING and CONFIRMED. Strong evidence and integrity failures can confirm immediately; otherwise consecutive suspicious observations are required before opening an incident. Repeated same-class events reuse an active incident rather than creating a new row for every point. This is basic persistence, not a fully tuned hysteresis policy. Genuine-weather events may also have monitor-only incidents; they never receive fault corrections.

Evidence strength is a normalized baseline evidence summary, **not a probability**. Isolation Forest scores are visible supporting novelty evidence. There is no production calibrated fusion model in this version. Some detector guardrails are hand-chosen baseline configuration and need calibration with representative station data.
