# Spatial engine

Station coordinates select candidate peers within a simple latitude/longitude window. This is a replaceable baseline, not a trained climate- or elevation-weighted station relationship graph. Up to 36 prior peer records are fetched with event time no later than the target. Peers with a latest suspicious observation are excluded; retained peers must have a recent trusted reading within 30 minutes. At least three peers are required; otherwise evidence is unavailable (`null`), not zero.

Compare T/P/RH changes against each station's historical baseline. Regional support requires at least two variables to change in the same direction and all variable change magnitudes to be reasonably aligned. This avoids mistaking ordinary regional diurnal changes for support for an isolated large temperature spike. Robust median peer changes reduce sensitivity to one faulty station. Absolute pressures from stations with different reference/elevation are not pooled into correction estimates.

A latitude/longitude window is only a first implementation. Geodesic distance, altitude/reference normalization for absolute pressure, measured historical correlation, lag-aware propagation, dynamic healthy-neighbor weighting and recovery hysteresis need implementation and real-data validation.
