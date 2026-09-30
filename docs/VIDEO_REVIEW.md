# Reference video review

Reference: [Next Wave Coders — SKYGUARD AI, SIH26073](https://www.youtube.com/watch?v=lz6KG9Cu-J8). Reviewed on 22 September 2026 using the available auto-generated transcript and visible demonstration frames. The transcript may contain transcription errors; claims below describe the presentation, not independently validated results.

The video introduces historical analysis and live monitoring around 0:32–0:55. Around 0:59–1:42 it describes a 2015–2024 NOAA archive covering six airport locations and location-specific Isolation Forest models. Around 1:45–2:19 it demonstrates periodically fetching observations, recording checks, and presenting recent measurements and anomaly scores. Around 2:19–2:39 it describes quality checks for frozen readings, sudden changes, reporting gaps and inconsistencies. The closing segment proposes a wider observation network.

## Adapted into this repository

- A dedicated Data workspace separates historical exploration from ongoing monitoring.
- History provides UTC date bounds, presets, hourly/daily means, min/mean/max statistics, two-station comparison, a paginated raw ledger and filtered CSV export.
- Monitoring provides receipt freshness, a rolling 30-observation feed, station filtering, manual refresh and optional 10-second UI refresh.
- The local simulated stream has start/pause controls, configurable minimum cycle intervals and a one-cycle action. Each simulation cycle advances the network by 10 minutes. Real mode shows incoming HTTP/MQTT-bridge data instead.
- Existing frozen/rate-of-change/temporal/spatial evidence remains available in station reports.
- The additive demo network has 198 stations and a 30-day hourly archive. Synthetic sites and archive records are explicitly labeled.

The video's ten-year dataset, sample totals, model performance and live provider integration are not represented as ours. We retain the user’s T/P/RH-only contract. Archive data is unscored and does not enter online detection histories or change old decisions. Derived physics remains derived, never an independent measurement.
