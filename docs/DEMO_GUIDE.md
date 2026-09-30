# Demonstration flow

1. Run `make dev`, open the dashboard and observe the Simulation badge. Initial data is explicitly synthetic.
2. Select Lucknow (AWS-IND-024). Open its station report. Compare raw temperature, expected range and T/P/RH-derived physics.
3. Open Evidence. Notice which sources are unavailable and that strength is not labeled probability.
4. Open Twin. Review a correction proposal; approve or reject it. Reopen History and verify the raw temperature remains unchanged.
5. Open Incidents. Set the incident to Investigating, save a reviewer note and add a reviewed feedback label. Check Timeline and Settings audit activity.
6. Open Scenario lab. Run temperature spike, then normal/recovery. Charts and decisions are recomputed from ordinary ingested observations. Run a regional pressure front to compare coherent T/P/RH change with an isolated fault. Classification is computed, not prefilled from the scenario name.
7. Test frozen humidity with at least 8 sampling steps; the detector uses elapsed duration. Run drift and inspect sensor health.
8. Disconnect cloud in Scenario lab. Run a fault scenario. Show the buffered packet count, then Reconnect & replay. Original timestamps remain in station history. This is a software emulator, not physical TinyML hardware.
9. Open Analytics. Explain synthetic benchmark scope, macro/per-class performance, abstentions and missing calibration. Do not imply near-perfect field accuracy.
10. Generate a JSON or CSV report. Explain that it is drawn from stored records rather than a fixed sample.

Scenarios operate on the existing timeline and intentionally do not erase previous history. Earlier scenarios can affect later results. For independently repeatable detector comparisons use `make evaluate`; for a fresh demo instance choose a different database path rather than deleting retained raw measurements. The demo clock only advances when scenarios run; it is not actual live telemetry.

### Mixed station states and fluctuating observations
Open Scenario lab → **Mixed network demonstration**. Selecting it defaults to 48 ten-minute steps (eight simulated hours) across the registered synthetic network. It appends observations; it does not rewrite history. The later steps introduce a shared southern T/P/RH front, isolated temperature spikes, moderate ambiguous changes, and dropped packets. The existing detector/heartbeat compute the final classes, so counts can vary with station coverage and prior context. This is a synthetic demonstration, not a benchmark accuracy claim.

Map status dots show green healthy, red sensor fault, blue genuine weather, gray data/communication issues, and purple review. Drag with the left mouse button or one finger to pan in both directions. Zoom reveals more dots; a representative of each present status stays visible in the sparse selection. Temperature/pressure/humidity layers remain optional.
