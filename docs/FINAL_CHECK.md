# Final verification — 2026-09-25

The implemented local demonstration passes the checks below. This is not certification that every possible input, deployment or hardware integration works.

| Area | Result and evidence |
|---|---|
| Backend | 51 pytest tests pass, using isolated temporary databases |
| Map logic | 2 marker visibility tests pass |
| Edge software | Host C++ rules, timestamps, FIFO replay and overflow checks pass |
| Frontend | TypeScript/Vite production build passes; existing bundle-size warning remains |
| Running API/proxy | 35 read-only API requests returned HTTP 200 with valid JSON/CSV through port 5173 |
| Database | SQLite quick_check returned ok; raw update/delete protection triggers remain installed |
| Map UI | 75 national dots → 103 after zoom; reset and compact card opened the correct station report |
| Stations | Lucknow search returned its single station card; all nine report tabs opened; Intelligence loaded telemetry, temporal stats, Virtual Buddy and detection layers |
| Incidents | Evidence, timeline and notes panels rendered; empty note cannot be saved; mutation safeguards covered in isolated tests where applicable |
| Analytics | Stored benchmark metrics, observation bars, categories and state health rendered |
| Data | Historical analysis, live feed and Dataset & ML results loaded; active/original editions remain selectable |
| Reports | All seven report endpoints and CSV/history exports succeeded; report cards rendered |
| Settings | Preferences, configuration, ingestion, model registry and audit panels rendered |
| Browser | No error-level console messages in the final verification tab |

The local servers were stopped when verification began. Restarted Downloads API on 8011 and frontend on 5173 with the matching proxy. The Desktop project was not touched. Continuous simulation remains paused. Verification did not inject observations or reviewer notes into the user's working database.

## Fix made during verification

Monitoring previously sorted full decision JSON across the joined dataset. It now selects the latest 30 IDs first, then retrieves only their decision payloads. Added a covering receipt-time/ID index. A regression test checks receipt ordering, the 30-row limit and exclusion of unscored archive records. A briefly attempted analytics expression index was removed after a restart compatibility problem; it is not part of the final change.

Observed local monitoring response improved from ~3.34 s to ~0.36 s in sequential checks, and was ~0.22 s in the final three-concurrent-request sweep. Analytics was ~3.55 s in that sweep (about 2 s in a warm sequential check); it remains a performance improvement opportunity. These are local spot measurements, not load-test guarantees.

## Limits that remain

- The stored 12,000-sample synthetic benchmark reports fault recall 75.1%, fault F1 0.858, macro F1 0.488 and genuine-weather recall 12.6%. It is not a fresh field evaluation or evidence that ML works perfectly. No benchmark artifacts were altered during this check.
- Regenerated historical samples are synthetic and unscored. They are not new ML validation evidence.
- Physical-board inference, real AWS/IMD feeds, MQTT with devices and production deployment remain unverified.
- Road detail depends on OpenStreetMap/Overpass availability. Last visual street-rendering check was the prior map implementation turn; this pass checked local map controls and navigation.
- Advanced calibration, sequence models, production access control and other gaps remain documented in LIMITATIONS.md.
