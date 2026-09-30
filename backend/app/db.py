import os
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Float, Integer, JSON, Text, event, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
(ROOT / 'data').mkdir(exist_ok=True)
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{ROOT / "data" / "skyguard.db"}')
# Render (and some other hosts) provide postgres:// but SQLAlchemy needs postgresql+psycopg://.
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False, 'timeout':30} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)

Session = sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase): pass
class Station(Base):
    __tablename__ = 'stations'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    metadata_json: Mapped[dict] = mapped_column(JSON)
    state_json: Mapped[dict] = mapped_column(JSON, default=dict)
class Raw(Base):
    __tablename__ = 'observations_raw'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    station_id: Mapped[str] = mapped_column(String(80), index=True)
    timestamp: Mapped[float] = mapped_column(Float, index=True)
    received_at: Mapped[float] = mapped_column(Float)
    payload: Mapped[dict] = mapped_column(JSON)
class Decision(Base):
    __tablename__ = 'anomaly_decisions'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    station_id: Mapped[str] = mapped_column(String(80), index=True)
    timestamp: Mapped[float] = mapped_column(Float, index=True)
    result: Mapped[dict] = mapped_column(JSON)
class Incident(Base):
    __tablename__ = 'incidents'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    station_id: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(30), default='OPEN')
    opened_at: Mapped[float] = mapped_column(Float, index=True)
    updated_at: Mapped[float] = mapped_column(Float)
    payload: Mapped[dict] = mapped_column(JSON)
class Correction(Base):
    __tablename__ = 'correction_candidates'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    observation_id: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(40), default='PROPOSED')
    payload: Mapped[dict] = mapped_column(JSON)
class Audit(Base):
    __tablename__ = 'audit_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[float] = mapped_column(Float)
    action: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict] = mapped_column(JSON)
class Setting(Base):
    __tablename__ = 'settings'
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
class Buffer(Base):
    __tablename__ = 'edge_buffer'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)

@event.listens_for(Raw, 'before_update')
@event.listens_for(Raw, 'before_delete')
def reject_raw_mutation(*args):
    raise ValueError('Raw observations are immutable')

def initialize():
    Base.metadata.create_all(engine)
    for table in (Raw.__table__,Decision.__table__):
        for index in table.indexes:index.create(engine,checkfirst=True)
    with engine.begin() as c:
        if engine.dialect.name == 'sqlite':
            c.exec_driver_sql('PRAGMA journal_mode=WAL')
            c.exec_driver_sql("CREATE TRIGGER IF NOT EXISTS raw_no_update BEFORE UPDATE ON observations_raw BEGIN SELECT RAISE(ABORT, 'Raw observations are immutable'); END")
            c.exec_driver_sql("CREATE TRIGGER IF NOT EXISTS raw_no_delete BEFORE DELETE ON observations_raw BEGIN SELECT RAISE(ABORT, 'Raw observations are immutable'); END")
        elif engine.dialect.name == 'postgresql':
            c.exec_driver_sql("CREATE OR REPLACE FUNCTION deny_raw_mutation() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Raw observations are immutable'; END; $$ LANGUAGE plpgsql")
            c.exec_driver_sql('DROP TRIGGER IF EXISTS raw_no_mutation ON observations_raw')
            c.exec_driver_sql('CREATE TRIGGER raw_no_mutation BEFORE UPDATE OR DELETE ON observations_raw FOR EACH ROW EXECUTE FUNCTION deny_raw_mutation()')

def now(): return datetime.now(timezone.utc).timestamp()
def iso(t): return datetime.fromtimestamp(t, timezone.utc).isoformat()
def audit(s, action, payload): s.add(Audit(timestamp=now(), action=action, payload=payload))
def get_setting(s, key, default):
    row = s.get(Setting, key)
    return row.value if row else default

def set_setting(s, key, value):
    row = s.get(Setting, key)
    if row: row.value = value
    else: s.add(Setting(key=key, value=value))

class BenchmarkPrediction(Base):
    __tablename__ = 'benchmark_predictions'
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    station_id: Mapped[str] = mapped_column(String(80), index=True)
    scenario: Mapped[str] = mapped_column(String(40), index=True)
    payload: Mapped[dict] = mapped_column(JSON)

Index("ix_raw_station_time", Raw.station_id, Raw.timestamp)
Index("ix_decision_station_time", Decision.station_id, Decision.timestamp)
Index("ix_raw_received", Raw.received_at)

# Cover the dashboard's scalar queries without reading large observation/evidence JSON blobs.
Index("ix_raw_receipt_id", Raw.received_at, Raw.id)
