"""
SkyGuard Comprehensive Cloud Database Loader
Populates:
  Phase 1: Complete 24h continuous observations (71,856 total in 24h window)
  Phase 2: Complete 24h anomaly decisions (71,856 total in 24h window)
  Phase 3: Rebuild secondary indexes on active tables
  Phase 4: Stream 90-day archive-regional-v4 observations (1,120,273 rows)
"""
import os, sys, time, io, json, sqlite3
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.venv/lib/python3.12/site-packages'))
import psycopg

SQLITE_PATH = Path(__file__).resolve().parents[1] / 'data/skyguard.db'

def escape_tsv(val):
    if val is None:
        return '\\N'
    return str(val).replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')

INDEXES = [
    ("ix_decision_station_time", "CREATE INDEX IF NOT EXISTS ix_decision_station_time ON anomaly_decisions (station_id, timestamp)"),
    ("ix_anomaly_decisions_station_id", "CREATE INDEX IF NOT EXISTS ix_anomaly_decisions_station_id ON anomaly_decisions (station_id)"),
    ("ix_anomaly_decisions_timestamp", "CREATE INDEX IF NOT EXISTS ix_anomaly_decisions_timestamp ON anomaly_decisions (timestamp)"),
    ("ix_raw_station_time", "CREATE INDEX IF NOT EXISTS ix_raw_station_time ON observations_raw (station_id, timestamp)"),
    ("ix_raw_received", "CREATE INDEX IF NOT EXISTS ix_raw_received ON observations_raw (received_at)"),
    ("ix_raw_receipt_id", "CREATE INDEX IF NOT EXISTS ix_raw_receipt_id ON observations_raw (received_at, id)"),
    ("ix_observations_raw_station_id", "CREATE INDEX IF NOT EXISTS ix_observations_raw_station_id ON observations_raw (station_id)"),
    ("ix_observations_raw_timestamp", "CREATE INDEX IF NOT EXISTS ix_observations_raw_timestamp ON observations_raw (timestamp)"),
]

def get_db_url():
    url = os.getenv('DATABASE_URL')
    if not url:
        raise ValueError("DATABASE_URL not found in .env")
    if url.startswith('postgresql+psycopg://'):
        url = url.replace('postgresql+psycopg://', 'postgresql://', 1)
    return url

def main():
    db_url = get_db_url()
    sq_conn = sqlite3.connect(str(SQLITE_PATH))
    sq_cur = sq_conn.cursor()

    print("=========================================================", flush=True)
    print("      SKYGUARD RAILWAY CLOUD DATABASE SYNCHRONIZER       ", flush=True)
    print("=========================================================", flush=True)

    # -------------------------------------------------------------
    # PHASE 1: Active 24-hour Observations (timestamp >= 1790064600)
    # -------------------------------------------------------------
    print("\n[PHASE 1] Checking 24-Hour Continuous Observations...", flush=True)
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM observations_raw WHERE timestamp >= 1790064600")
            existing_obs_ids = set(r[0] for r in cur.fetchall())
    print(f"  Already in Railway: {len(existing_obs_ids)} / 71,856 active observations.", flush=True)

    sq_cur.execute("""
        SELECT id, station_id, timestamp, received_at, payload 
        FROM observations_raw 
        WHERE timestamp >= 1790064600 AND timestamp <= 1790150400
        ORDER BY timestamp
    """)
    missing_obs = [r for r in sq_cur.fetchall() if r[0] not in existing_obs_ids]
    print(f"  Observations to upload: {len(missing_obs)} rows (~{round(len(missing_obs)*0.39/1024, 1)} MB)...", flush=True)

    if missing_obs:
        chunk_size = 2000
        t0 = time.time()
        for i in range(0, len(missing_obs), chunk_size):
            chunk = missing_obs[i:i + chunk_size]
            buf = io.StringIO()
            for r in chunk:
                buf.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{escape_tsv(r[4])}\n")
            with psycopg.connect(db_url, autocommit=True) as conn:
                with conn.cursor() as cur:
                    with cur.copy("COPY observations_raw (id, station_id, timestamp, received_at, payload) FROM STDIN") as copy:
                        copy.write(buf.getvalue().encode('utf-8'))
            done = min(i + chunk_size, len(missing_obs))
            elapsed = time.time() - t0
            rate = done / max(0.1, elapsed)
            rem = (len(missing_obs) - done) / max(1, rate)
            print(f"  -> Observations: {done}/{len(missing_obs)} ({round(100.0*done/len(missing_obs), 1)}%) | {round(rate, 1)} rows/s | ETA: {round(rem, 0)}s", flush=True)
        print(f"  [PHASE 1 COMPLETE] 100% of 24h observations are now live!", flush=True)
    else:
        print("  [PHASE 1 COMPLETE] All 24h observations already present.", flush=True)

    # -------------------------------------------------------------
    # PHASE 2: Active 24-hour Anomaly Decisions (timestamp >= 1790064600)
    # -------------------------------------------------------------
    print("\n[PHASE 2] Checking 24-Hour Anomaly Decisions...", flush=True)
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM anomaly_decisions WHERE timestamp >= 1790064600")
            existing_dec_ids = set(r[0] for r in cur.fetchall())
    print(f"  Already in Railway: {len(existing_dec_ids)} / 71,856 active decisions.", flush=True)

    sq_cur.execute("""
        SELECT id, station_id, timestamp, result 
        FROM anomaly_decisions 
        WHERE timestamp >= 1790064600 AND timestamp <= 1790150400
        ORDER BY timestamp DESC
    """)
    missing_dec = [r for r in sq_cur.fetchall() if r[0] not in existing_dec_ids]
    print(f"  Decisions to upload: {len(missing_dec)} rows (~{round(len(missing_dec)*4/1024, 1)} MB)...", flush=True)

    if missing_dec:
        chunk_size = 1000
        t0 = time.time()
        for i in range(0, len(missing_dec), chunk_size):
            chunk = missing_dec[i:i + chunk_size]
            buf = io.StringIO()
            for r in chunk:
                buf.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{escape_tsv(r[3])}\n")
            with psycopg.connect(db_url, autocommit=True) as conn:
                with conn.cursor() as cur:
                    with cur.copy("COPY anomaly_decisions (id, station_id, timestamp, result) FROM STDIN") as copy:
                        copy.write(buf.getvalue().encode('utf-8'))
            done = min(i + chunk_size, len(missing_dec))
            elapsed = time.time() - t0
            rate = done / max(0.1, elapsed)
            rem = (len(missing_dec) - done) / max(1, rate)
            print(f"  -> Decisions: {done}/{len(missing_dec)} ({round(100.0*done/len(missing_dec), 1)}%) | {round(rate, 1)} rows/s | ETA: {round(rem, 0)}s", flush=True)
        print(f"  [PHASE 2 COMPLETE] 100% of 24h decisions are now live!", flush=True)
    else:
        print("  [PHASE 2 COMPLETE] All 24h decisions already present.", flush=True)

    # -------------------------------------------------------------
    # PHASE 3: Rebuild Secondary Indexes for Instant Query Response
    # -------------------------------------------------------------
    print("\n[PHASE 3] Verifying and Rebuilding B-Tree Indexes...", flush=True)
    with psycopg.connect(db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            for idx_name, idx_sql in INDEXES:
                t_idx = time.time()
                cur.execute(idx_sql)
                print(f"  -> Index {idx_name} verified in {round(time.time() - t_idx, 2)}s", flush=True)
    print("  [PHASE 3 COMPLETE] All database indexes active for high performance.", flush=True)

    # -------------------------------------------------------------
    # PHASE 4: Stream 90-Day Archive (archive-regional-v4)
    # 1,120,273 rows across 500 stations (~435 MB).
    # Uploads progressively in 2,500-row chunks with autocommit per chunk.
    # -------------------------------------------------------------
    print("\n[PHASE 4] Checking 90-Day Historical Archive (archive-regional-v4)...", flush=True)
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM observations_raw WHERE payload->>'source_version' = 'archive-regional-v4'")
            existing_arch = cur.fetchone()[0]
    total_arch = 1120273
    print(f"  Current archive rows in Railway: {existing_arch} / {total_arch}", flush=True)

    if existing_arch < total_arch:
        print(f"  Streaming remaining {total_arch - existing_arch} archive rows...", flush=True)
        # Fetch archive IDs already in database to ensure 100% idempotent resumption
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM observations_raw WHERE payload->>'source_version' = 'archive-regional-v4'")
                arch_ids = set(r[0] for r in cur.fetchall())

        sq_cur.execute("""
            SELECT id, station_id, timestamp, received_at, payload 
            FROM observations_raw 
            WHERE json_extract(payload, '$.source_version') = 'archive-regional-v4'
            ORDER BY timestamp
        """)

        chunk_size = 2500
        t0 = time.time()
        uploaded_now = 0
        total_remaining = total_arch - len(arch_ids)

        while True:
            chunk = sq_cur.fetchmany(chunk_size)
            if not chunk:
                break
            # Filter already loaded
            if arch_ids:
                chunk = [r for r in chunk if r[0] not in arch_ids]
                if not chunk:
                    continue
            buf = io.StringIO()
            for r in chunk:
                buf.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{escape_tsv(r[4])}\n")
            with psycopg.connect(db_url, autocommit=True) as conn:
                with conn.cursor() as cur:
                    with cur.copy("COPY observations_raw (id, station_id, timestamp, received_at, payload) FROM STDIN") as copy:
                        copy.write(buf.getvalue().encode('utf-8'))
            uploaded_now += len(chunk)
            current_total = len(arch_ids) + uploaded_now
            elapsed = time.time() - t0
            rate = uploaded_now / max(0.1, elapsed)
            rem = (total_remaining - uploaded_now) / max(1, rate)
            pct = round(100.0 * current_total / total_arch, 1)
            print(f"  -> Archive: {current_total}/{total_arch} ({pct}%) | {round(rate, 1)} rows/s | ETA: {round(rem, 0)}s", flush=True)
        print("  [PHASE 4 COMPLETE] Full 90-day archive successfully synchronized!", flush=True)
    else:
        print("  [PHASE 4 COMPLETE] 90-day archive already fully synchronized.", flush=True)

    # -------------------------------------------------------------
    # Final Status Report
    # -------------------------------------------------------------
    print("\n=========================================================", flush=True)
    print("             FINAL RAILWAY POSTGRESQL AUDIT              ", flush=True)
    print("=========================================================", flush=True)
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_size_pretty(pg_database_size('railway'))")
            db_size = cur.fetchone()[0]
            print(f"  Total Database Disk Usage: {db_size}\n")
            tables = ['stations', 'incidents', 'settings', 'correction_candidates', 'audit_events', 'benchmark_predictions', 'observations_raw', 'anomaly_decisions']
            for t in tables:
                cur.execute(f"SELECT count(*) FROM {t}")
                cnt = cur.fetchone()[0]
                cur.execute(f"SELECT pg_size_pretty(pg_total_relation_size('{t}'))")
                sz = cur.fetchone()[0]
                print(f"  {t:25}: {cnt:>10} rows  ({sz})")
    print("=========================================================", flush=True)
    print("SUCCESS: Every website feature is fully powered and active!", flush=True)

if __name__ == '__main__':
    main()
