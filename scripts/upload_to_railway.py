"""Upload 500 stations, incidents, corrections, settings, and observations to Railway PostgreSQL."""
import os, sys, json, sqlite3, time
from pathlib import Path

# Load .env
ENV_PATH = Path(__file__).resolve().parents[1] / '.env'
if ENV_PATH.exists():
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith('DATABASE_URL='):
                val = line.split('=', 1)[1].strip()
                os.environ['DATABASE_URL'] = val
                break

# Add venv packages so psycopg is available
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.venv/lib/python3.12/site-packages'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg

SQLITE_PATH = Path(__file__).resolve().parents[1] / 'data/skyguard.db'

def main():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not found in environment or .env file")
    
    if db_url.startswith('postgresql+psycopg://'):
        db_url = db_url.replace('postgresql+psycopg://', 'postgresql://', 1)

    print(f"Connecting to Railway PostgreSQL: {db_url[:35]}...")
    sq_conn = sqlite3.connect(str(SQLITE_PATH))
    sq_conn.row_factory = sqlite3.Row
    sq_cur = sq_conn.cursor()

    pg_conn = psycopg.connect(db_url, autocommit=True)
    pg_cur = pg_conn.cursor()
    print("Connected successfully.")

    # 1. Copy stations (500 rows)
    print("\n1. Copying stations (500 rows)...")
    sq_cur.execute("SELECT id, metadata_json, state_json FROM stations ORDER BY id")
    stations = sq_cur.fetchall()
    pg_cur.executemany(
        "INSERT INTO stations (id, metadata_json, state_json) VALUES (%s, %s, %s) ON CONFLICT (id) DO UPDATE SET metadata_json=EXCLUDED.metadata_json, state_json=EXCLUDED.state_json",
        [tuple(r) for r in stations]
    )
    print(f"   Done: {len(stations)} stations uploaded.")

    # 2. Copy incidents (487 rows)
    print("\n2. Copying incidents (487 rows)...")
    sq_cur.execute("SELECT id, station_id, status, opened_at, updated_at, payload FROM incidents ORDER BY opened_at")
    incidents = sq_cur.fetchall()
    pg_cur.executemany(
        "INSERT INTO incidents (id, station_id, status, opened_at, updated_at, payload) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        [tuple(r) for r in incidents]
    )
    print(f"   Done: {len(incidents)} incidents uploaded.")

    # 3. Copy correction candidates (247 rows)
    print("\n3. Copying correction candidates (247 rows)...")
    sq_cur.execute("SELECT id, observation_id, status, payload FROM correction_candidates")
    corrections = sq_cur.fetchall()
    pg_cur.executemany(
        "INSERT INTO correction_candidates (id, observation_id, status, payload) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        [tuple(r) for r in corrections]
    )
    print(f"   Done: {len(corrections)} correction candidates uploaded.")

    # 4. Copy audit events (541 rows)
    print("\n4. Copying audit events (541 rows)...")
    sq_cur.execute("SELECT id, timestamp, action, payload FROM audit_events ORDER BY id")
    audits = sq_cur.fetchall()
    pg_cur.executemany(
        "INSERT INTO audit_events (id, timestamp, action, payload) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        [tuple(r) for r in audits]
    )
    print(f"   Done: {len(audits)} audit events uploaded.")

    # 5. Copy settings (8 rows)
    print("\n5. Copying settings...")
    sq_cur.execute("SELECT key, value FROM settings")
    settings = sq_cur.fetchall()
    pg_cur.executemany(
        "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value",
        [tuple(r) for r in settings]
    )
    print(f"   Done: {len(settings)} settings uploaded.")

    # 6. Copy simulator observations_raw (112,129 rows in batches)
    print("\n6. Copying simulator observations_raw (112,129 rows)...")
    sq_cur.execute("SELECT id, station_id, timestamp, received_at, payload FROM observations_raw WHERE json_extract(payload, '$.source') != 'synthetic_archive' ORDER BY timestamp")
    batch = []
    inserted_obs = 0
    t0 = time.time()
    while True:
        rows = sq_cur.fetchmany(3000)
        if not rows:
            break
        pg_cur.executemany(
            "INSERT INTO observations_raw (id, station_id, timestamp, received_at, payload) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            [tuple(r) for r in rows]
        )
        inserted_obs += len(rows)
        print(f"   Observations uploaded: {inserted_obs}/112129 ({round(time.time()-t0, 1)}s)...")
    print(f"   Done: {inserted_obs} observations uploaded in {round(time.time()-t0, 1)}s.")

    # 7. Copy anomaly decisions (112,129 rows in batches)
    print("\n7. Copying anomaly decisions (112,129 rows)...")
    sq_cur.execute("SELECT id, station_id, timestamp, result FROM anomaly_decisions ORDER BY timestamp")
    batch = []
    inserted_dec = 0
    t0 = time.time()
    while True:
        rows = sq_cur.fetchmany(3000)
        if not rows:
            break
        pg_cur.executemany(
            "INSERT INTO anomaly_decisions (id, station_id, timestamp, result) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            [tuple(r) for r in rows]
        )
        inserted_dec += len(rows)
        print(f"   Decisions uploaded: {inserted_dec}/112129 ({round(time.time()-t0, 1)}s)...")
    print(f"   Done: {inserted_dec} decisions uploaded in {round(time.time()-t0, 1)}s.")

    # 8. Verification
    print("\n================ FINAL RAILWAY STATUS ================")
    for t in ['stations', 'incidents', 'settings', 'correction_candidates', 'audit_events', 'observations_raw', 'anomaly_decisions']:
        pg_cur.execute(f"SELECT count(*) FROM {t}")
        cnt = pg_cur.fetchone()[0]
        print(f"  {t:25}: {cnt:>8} rows")

    pg_cur.close()
    pg_conn.close()
    sq_conn.close()
    print("\nSUCCESS: All data successfully synced to Railway PostgreSQL!")

if __name__ == '__main__':
    main()
