# Future physical AWS / IMD integration

No IMD account, API key, live endpoint or real station dataset was supplied. None is accessed or impersonated. The project follows the supplied T/P/RH brief, not an independently verified government integration contract.

Map upstream fields into the canonical observation schema, register station cadence and pressure-reference metadata, and preserve stable packet IDs and event timestamps. Start with a separate live database and known QA data, then connect HTTP or the optional MQTT bridge. Verify instrument units, timezone, missing codes, calibration, station pressure versus MSL, elevation, cadence and sequence semantics with the upstream owner.

Before public or institutional deployment: implement operator identity/RBAC, per-device credentials, secret rotation, TLS, distributed ingestion control, migrations/backups, retention, redelivery guarantees, site monitoring, load/recovery tests, and an operational correction-publication policy. These are not implied by the local demo API key.
