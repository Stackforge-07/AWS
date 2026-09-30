from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
import math

VARIABLES = ('temperature_c', 'pressure_hpa', 'relative_humidity_pct')
class Classification(StrEnum):
    NORMAL = 'NORMAL'
    GENUINE_WEATHER = 'GENUINE_WEATHER'
    SENSOR_FAULT = 'SENSOR_FAULT'
    DATA_COMMS_ISSUE = 'DATA_COMMS_ISSUE'
    BOTH_COMPLEX = 'BOTH_COMPLEX'
    UNKNOWN_REVIEW = 'UNKNOWN_REVIEW'

class Observation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    observation_id: str = Field(min_length=1, max_length=100)
    station_id: str = Field(min_length=1, max_length=80)
    timestamp_utc: datetime
    temperature_c: float
    pressure_hpa: float
    relative_humidity_pct: float
    sequence_number: int | None = Field(default=None, ge=0)
    source: Literal['rest', 'csv', 'simulator', 'mqtt', 'edge_replay', 'websocket', 'synthetic_archive'] = 'rest'
    source_version: str | None = Field(default=None,max_length=80)
    edge_state: Literal['EDGE_NORMAL', 'EDGE_SUSPICIOUS', 'EDGE_CRITICAL'] | None = None
    edge_anomaly_score: float | None = Field(default=None, ge=0)
    edge_model_version: str | None = None

    @field_validator('temperature_c', 'pressure_hpa', 'relative_humidity_pct')
    @classmethod
    def finite(cls, v):
        if not math.isfinite(v):
            raise ValueError('Measurement must be finite')
        return v

    @field_validator('timestamp_utc')
    @classmethod
    def aware(cls, v):
        if v.tzinfo is None:
            raise ValueError('Timestamp must include timezone')
        return v.astimezone(timezone.utc)

class StationInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(pattern=r'^[A-Za-z0-9_-]{1,80}$')
    city: str = Field(max_length=100)
    state: str = Field(max_length=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    elevation_m: float = 0
    cadence_seconds: int = Field(default=600, ge=1, le=86400)
    pressure_reference: Literal['station', 'MSL'] = 'station'
    network: str = 'User AWS'

class IncidentUpdate(BaseModel):
    status: Literal['OPEN', 'ACKNOWLEDGED', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE'] | None = None
    note: str | None = Field(default=None, max_length=4000)
    feedback: Literal['SENSOR_FAULT','GENUINE_WEATHER','FALSE_POSITIVE','MAINTENANCE_CONFIRMED','UNKNOWN'] | None = None

class ScenarioInput(BaseModel):
    scenario: Literal['mixed_network','normal','temperature_spike','pressure_spike','humidity_spike','temperature_drift','pressure_drift','humidity_drift','frozen_humidity','frozen_temperature','frozen_pressure','communication_outage','regional_front','extreme_heat','ambiguous_local','multi_sensor_fault','faulty_neighbor','noise','offset','missing_packets','duplicate_packet','out_of_order','timestamp_error','recovery']
    station_id: str = 'AWS-IND-024'
    steps: int = Field(default=12, ge=1, le=48)
    seed: int = Field(default=26073, ge=0)

class SettingsInput(BaseModel):
    operator_name: str = Field(default='Demo operator', min_length=1, max_length=100)
    auto_refresh: bool = True
    stale_multiplier: int = Field(default=3, ge=2, le=12)
