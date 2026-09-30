# Reference research and implementation — 23 September 2026

The supplied screenshots show Anuruddha Pratap’s [SkyGuard / HashCoders LinkedIn post](https://www.linkedin.com/posts/anuruddha-pratap_sih2026-smartindiahackathon-skyguardai-ugcPost-7508539355448225793-a78x/). A strongly matching public team repository is [bhanu-agrawal/SIHV1.2](https://github.com/bhanu-agrawal/SIHV1.2), inspected at commit `665f605280594dc10a71cf7de5115c839a98fa9f`. Bhanu Agrawal is named among the teammates in the post. This is a matching team reference, not a verified personal repository belonging to Anuruddha.

No declared repository license was found. No reference source code, weights, datasets, assets or claimed benchmark metrics were imported. The additions here independently implement the described capabilities using this project’s existing observations and evidence contracts.

| Reference capability | Local implementation |
| --- | --- |
| Searchable station cards and health tiers | Stations → Station cards, paginated and filtered by healthy/watch/degraded; actual latest T/P/RH and report links |
| Current snapshot and telemetry | Station report → Intelligence; source/version, recorded readings, packet age and 24-hour completeness |
| Temporal and sensor-health analysis | Prior trusted sample statistics, classical and robust z-scores, recorded rates and flatline evidence |
| Virtual Buddy | Read-only nearby-station tendency context with fresh trusted peers, distances, ages and minimum evidence requirements |
| Layered diagnosis and explanations | Existing recorded ML/temporal/physics/spatial/twin evidence displayed together with the stored recommendation |
| Historical parameter charts | Sensors: 1h/6h/24h/7d/30d; all parameters or individual T/P/RH; exact stored observations and actual correction candidate markers |
| Local station location | On-demand OpenStreetMap street map and external location link |
| Evaluation metrics | Existing reproducible local benchmark dashboards retained; reference scores are not reused |

## Scope and scientific boundaries

The revised T/P/RH contract explicitly excludes NWP and external forecasts. Consequently the reference’s NWP component is not implemented. Virtual Buddy is an uncalibrated investigative estimate (own past baseline plus median peer change), not a new model, independent sensor, approved correction or revision to an immutable decision. It requires at least six trusted own-history samples and three fresh trusted neighbors of the same source version. It uses the existing geographical candidate window; terrain/correlation-weighted selection and operational field validation remain future work.

Charts do not invent expected bands for unscored archive observations. Green markers are actual stored proposed/approved correction candidates; raw measurements remain intact. Health tiers use the existing operational health index, not failure probability. The active local data remains synthetic.
