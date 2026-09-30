# Virtual weather twin

The deployed baseline projects the most recent trusted station value using a median local slope, with a bounded time horizon. Each T/P/RH prediction carries a heuristic range based on recent variability and explicit scale floors. It uses only past observations. Reliability is MEDIUM only when enough trusted station history and fresh peers are available; otherwise LOW. There is no HIGH reliability claim in this version.

The UI compares observed and expected values and shows residuals. All ranges are explicitly **uncalibrated**. Spatial estimates independently gate correction proposals; they are not falsely treated as independent votes from a twin derived from the same sources. Seasonal history and ML forecast sources are marked unavailable.

The broader ensemble twin described in the brief (seasonality, trained forecasting, multivariate models, uncertainty calibration) remains a future extension. NWP is excluded by the revised input contract.
