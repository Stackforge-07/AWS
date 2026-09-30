# History and monitoring

Open **Data** or **History & monitoring** in the application.

## Historical analysis

Select a station and optional comparison station. Date inputs use UTC calendar days: From is inclusive, Through includes the complete day. Presets anchor to the selected station's latest stored observation, which can differ from wall-clock time in simulation. Ledger timestamps use the browser's local timezone; chart labels use UTC. Hourly/daily values are arithmetic means; statistics use all matching raw samples. No resampling creates raw observations.

The API `/api/v1/history/{station_id}` accepts timezone-aware `start`, exclusive `end`, `page`, `page_size` (1–200), `bucket=hour|day`, and `source=all|archive|processed`. It returns counts, bounds, aggregates and newest-first ledger rows. `/export` accepts the same dates/source and exports all matching rows up to the interactive query limit of 150,000 records per station. Narrow the range if that limit is exceeded. Export includes source, classification and receipt time; spreadsheet formula prefixes are escaped.

A one-time transactional simulation migration adds 144 sites inside the bundled polygons, 30 days × 24 hourly unscored samples for all 198 synthetic stations, and eight processed warm-up observations for each new site. It never overwrites previous raw rows or decisions. `archive_expansion_v1` records completion; restarts do not repeat it. Generated site coordinates do not identify physical weather installations. Their elevation and climatology are demonstration values. Existing detector training artifacts are unchanged.

## Live monitoring

The screen follows the actual ingestion database. Auto-refresh checks the API every ten seconds; pausing this refresh does not stop a running simulated stream. **Pause stream** stops generation. **Sample once** processes one new network cycle. Starting a stream generates normal correlated synthetic T/P/RH; use the scenario lab to inject faults. Cycle interval is a minimum delay from the completion of the last cycle, with up to ten seconds scheduler granularity, plus processing time. One worker is required.

The monitor shows the latest 30 processed arrivals, optionally filtered by station. Receipt totals exclude the archive import. The simulation clock is independent of wall time and is displayed explicitly. On server restart, generation is paused. A cycle error pauses the stream and is displayed; the transaction rolls back rather than storing partial cycles.

In `SKYGUARD_MODE=live`, generation endpoints reject requests. Register stations and send real observations through the existing authenticated ingestion endpoints or configured MQTT bridge. This change does not connect NOAA, IMD or another external telemetry provider. There is no claim of a live national sensor feed.

## Optional larger dataset

`make expand-dataset` grows the local network to 500 sites and extends hourly archive coverage to 90 days. The script is resumable per station. Newly commissioned sites receive one online diagnostic sample and can remain in cold-start review until additional stream cycles arrive; previously populated sites retain their history. The larger offline benchmark uses separate 48-hour causal warm-up windows, not the station current-state cache. See EVALUATION.md for the test design and interpretation.
