"""
testing_app/models.py
SQLAlchemy models for the testing app.
Re-uses the same db instance and maps to the same tables
created by models_v3.py (no duplicate table definitions).
"""
from datetime import datetime
try:
    from testing_app.extensions import db
except ImportError:
    from extensions import db  # noqa: F401



class TestSession(db.Model):
    __tablename__ = 'test_sessions'
    id                = db.Column(db.Integer, primary_key=True)
    session_code      = db.Column(db.String(50), nullable=False, unique=True)
    operator_name     = db.Column(db.String(150), nullable=False)
    operator_email    = db.Column(db.String(150))
    access_request_id = db.Column(db.Integer)
    valve_id          = db.Column(db.String(100))
    valve_type        = db.Column(db.String(100))
    valve_size        = db.Column(db.String(50))
    client_name       = db.Column(db.String(200))
    job_number        = db.Column(db.String(100))
    test_type         = db.Column(db.String(50), nullable=False, default='standard')
    medium            = db.Column(db.String(50), nullable=False, default='water')
    target_pressure   = db.Column(db.Numeric(8, 2))
    target_duration   = db.Column(db.Integer)
    temperature_limit = db.Column(db.Numeric(5, 2))
    status            = db.Column(db.String(20), nullable=False, default='setup')
    started_at        = db.Column(db.DateTime)
    ended_at          = db.Column(db.DateTime)
    duration_seconds  = db.Column(db.Integer)
    result            = db.Column(db.String(20))
    notes             = db.Column(db.Text)
    reviewed_by       = db.Column(db.String(150))
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at        = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    readings      = db.relationship('TestReading', backref='session', lazy=True, cascade='all, delete-orphan')
    result_record = db.relationship('TestResult',  backref='session', uselist=False, cascade='all, delete-orphan')

    def _f(self, v): return float(v) if v is not None else None

    def to_dict(self):
        return {
            'id': self.id, 'session_code': self.session_code,
            'operator_name': self.operator_name,
            'valve_id': self.valve_id, 'valve_type': self.valve_type,
            'valve_size': self.valve_size, 'client_name': self.client_name,
            'job_number': self.job_number, 'test_type': self.test_type,
            'medium': self.medium,
            'target_pressure': self._f(self.target_pressure),
            'target_duration': self.target_duration,
            'temperature_limit': self._f(self.temperature_limit),
            'status': self.status, 'result': self.result, 'notes': self.notes,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat(),
        }


class TestReading(db.Model):
    __tablename__ = 'test_readings'
    id             = db.Column(db.BigInteger, primary_key=True)
    session_id     = db.Column(db.Integer, db.ForeignKey('test_sessions.id', ondelete='CASCADE'), nullable=False)
    recorded_at    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pressure_bar   = db.Column(db.Numeric(8, 3))
    temperature_c  = db.Column(db.Numeric(6, 2))
    flow_rate_lpm  = db.Column(db.Numeric(8, 3))
    leakage_ml_min = db.Column(db.Numeric(8, 3))
    rpm            = db.Column(db.Numeric(7, 2))
    pressure_alert = db.Column(db.String(10), default='ok')
    temp_alert     = db.Column(db.String(10), default='ok')
    leakage_alert  = db.Column(db.String(10), default='ok')

    def _f(self, v): return float(v) if v is not None else None

    def to_dict(self):
        return {
            'id': self.id, 'session_id': self.session_id,
            'recorded_at': self.recorded_at.isoformat(),
            'pressure_bar': self._f(self.pressure_bar),
            'temperature_c': self._f(self.temperature_c),
            'flow_rate_lpm': self._f(self.flow_rate_lpm),
            'leakage_ml_min': self._f(self.leakage_ml_min),
            'rpm': self._f(self.rpm),
            'pressure_alert': self.pressure_alert,
            'temp_alert': self.temp_alert,
            'leakage_alert': self.leakage_alert,
        }


class TestResult(db.Model):
    __tablename__ = 'test_results'
    id                    = db.Column(db.Integer, primary_key=True)
    session_id            = db.Column(db.Integer, db.ForeignKey('test_sessions.id', ondelete='CASCADE'), nullable=False, unique=True)
    max_pressure_bar      = db.Column(db.Numeric(8, 3))
    min_pressure_bar      = db.Column(db.Numeric(8, 3))
    avg_pressure_bar      = db.Column(db.Numeric(8, 3))
    max_temperature_c     = db.Column(db.Numeric(6, 2))
    avg_flow_rate_lpm     = db.Column(db.Numeric(8, 3))
    max_leakage_ml_min    = db.Column(db.Numeric(8, 3))
    pressure_hold_ok      = db.Column(db.Boolean)
    leakage_within_limit  = db.Column(db.Boolean)
    temperature_ok        = db.Column(db.Boolean)
    pressure_limit_bar    = db.Column(db.Numeric(8, 3))
    leakage_limit_ml_min  = db.Column(db.Numeric(8, 3))
    duration_achieved_sec = db.Column(db.Integer)
    ai_summary            = db.Column(db.Text)
    ai_anomalies          = db.Column(db.JSON, default=list)
    ai_confidence         = db.Column(db.Numeric(4, 2))
    pdf_url               = db.Column(db.String(500))
    csv_url               = db.Column(db.String(500))
    engineer_signed_by    = db.Column(db.String(150))
    signed_at             = db.Column(db.DateTime)
    created_at            = db.Column(db.DateTime, default=datetime.utcnow)

    def _f(self, v): return float(v) if v is not None else None

    def to_dict(self):
        return {
            'id': self.id, 'session_id': self.session_id,
            'max_pressure_bar': self._f(self.max_pressure_bar),
            'min_pressure_bar': self._f(self.min_pressure_bar),
            'avg_pressure_bar': self._f(self.avg_pressure_bar),
            'max_temperature_c': self._f(self.max_temperature_c),
            'avg_flow_rate_lpm': self._f(self.avg_flow_rate_lpm),
            'max_leakage_ml_min': self._f(self.max_leakage_ml_min),
            'pressure_hold_ok': self.pressure_hold_ok,
            'leakage_within_limit': self.leakage_within_limit,
            'temperature_ok': self.temperature_ok,
            'ai_summary': self.ai_summary,
            'ai_anomalies': self.ai_anomalies or [],
            'ai_confidence': self._f(self.ai_confidence),
            'pdf_url': self.pdf_url, 'csv_url': self.csv_url,
            'engineer_signed_by': self.engineer_signed_by,
            'created_at': self.created_at.isoformat(),
        }


class TestSettings(db.Model):
    __tablename__ = 'test_settings'
    id                   = db.Column(db.Integer, primary_key=True)
    machine_id           = db.Column(db.String(50))
    max_pressure_bar     = db.Column(db.Numeric(8, 2))
    min_pressure_bar     = db.Column(db.Numeric(8, 2))
    pressure_warning_pct = db.Column(db.Integer)
    max_leakage_ml_min   = db.Column(db.Numeric(8, 3))
    leakage_warning_ml   = db.Column(db.Numeric(8, 3))
    max_temp_c           = db.Column(db.Numeric(6, 2))
    temp_warning_c       = db.Column(db.Numeric(6, 2))
    default_duration_sec = db.Column(db.Integer)
    reading_interval_ms  = db.Column(db.Integer)
    ai_enabled           = db.Column(db.Boolean)
    ai_model             = db.Column(db.String(100))
    ai_sensitivity       = db.Column(db.String(20))
    last_calibrated_at   = db.Column(db.DateTime)
    calibrated_by        = db.Column(db.String(150))
    calibration_notes    = db.Column(db.Text)
    updated_at           = db.Column(db.DateTime)

    @classmethod
    def get(cls):
        return cls.query.get(1)

    def _f(self, v): return float(v) if v is not None else None

    def to_dict(self):
        return {
            'machine_id': self.machine_id,
            'max_pressure_bar': self._f(self.max_pressure_bar),
            'min_pressure_bar': self._f(self.min_pressure_bar),
            'pressure_warning_pct': self.pressure_warning_pct,
            'max_leakage_ml_min': self._f(self.max_leakage_ml_min),
            'leakage_warning_ml': self._f(self.leakage_warning_ml),
            'max_temp_c': self._f(self.max_temp_c),
            'temp_warning_c': self._f(self.temp_warning_c),
            'default_duration_sec': self.default_duration_sec,
            'reading_interval_ms': self.reading_interval_ms,
            'ai_enabled': self.ai_enabled,
            'ai_model': self.ai_model,
            'ai_sensitivity': self.ai_sensitivity,
            'last_calibrated_at': self.last_calibrated_at.isoformat() if self.last_calibrated_at else None,
            'calibrated_by': self.calibrated_by,
            'calibration_notes': self.calibration_notes,
        }
