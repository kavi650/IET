"""
models_v3.py  — New SQLAlchemy models for platform v3 expansion.
Imported at the bottom of models.py via:  from models_v3 import *
All models share the same `db` instance from models.py.
"""
from datetime import datetime
from models import db


# ============================================================
# Section A — Public Website Content
# ============================================================

class Project(db.Model):
    """Case studies / client project showcase."""
    __tablename__ = 'projects'

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    client_name  = db.Column(db.String(200))
    industry     = db.Column(db.String(100))
    problem      = db.Column(db.Text)
    solution     = db.Column(db.Text)
    result       = db.Column(db.Text)
    image_url    = db.Column(db.String(500))
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    sort_order   = db.Column(db.Integer, nullable=False, default=0)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'client_name': self.client_name,
            'industry': self.industry, 'problem': self.problem,
            'solution': self.solution, 'result': self.result,
            'image_url': self.image_url, 'is_published': self.is_published,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat(),
        }


class Download(db.Model):
    """Downloadable files — brochures, datasheets, technical PDFs."""
    __tablename__ = 'downloads'

    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(200), nullable=False)
    description    = db.Column(db.Text)
    category       = db.Column(db.String(50), nullable=False, default='brochure')
    # 'brochure' | 'datasheet' | 'technical' | 'certificate'
    file_url       = db.Column(db.String(500), nullable=False)
    file_size_kb   = db.Column(db.Integer)
    is_published   = db.Column(db.Boolean, nullable=False, default=True)
    download_count = db.Column(db.Integer, nullable=False, default=0)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    VALID_CATEGORIES = ('brochure', 'datasheet', 'technical', 'certificate')

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'description': self.description,
            'category': self.category, 'file_url': self.file_url,
            'file_size_kb': self.file_size_kb, 'is_published': self.is_published,
            'download_count': self.download_count,
            'created_at': self.created_at.isoformat(),
        }


class Industry(db.Model):
    """Industries served — displayed on the public Industries page."""
    __tablename__ = 'industries'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    slug        = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    icon        = db.Column(db.String(50))
    image_url   = db.Column(db.String(500))
    sort_order  = db.Column(db.Integer, nullable=False, default=0)
    is_active   = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'slug': self.slug,
            'description': self.description, 'icon': self.icon,
            'image_url': self.image_url, 'sort_order': self.sort_order,
            'is_active': self.is_active,
        }


# ============================================================
# Section B — Testing Access Control
# ============================================================

class TestingAccessRequest(db.Model):
    """Access requests submitted by public users for testing software."""
    __tablename__ = 'testing_access_requests'

    id               = db.Column(db.Integer, primary_key=True)
    full_name        = db.Column(db.String(150), nullable=False)
    email            = db.Column(db.String(150), nullable=False)
    company_name     = db.Column(db.String(200))
    phone            = db.Column(db.String(30))
    purpose          = db.Column(db.Text)
    status           = db.Column(db.String(20), nullable=False, default='pending')
    # 'pending' | 'approved' | 'rejected'
    approved_by      = db.Column(db.String(100))
    rejection_note   = db.Column(db.Text)
    access_token     = db.Column(db.String(64), unique=True)
    token_expires_at = db.Column(db.DateTime)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    actioned_at      = db.Column(db.DateTime)

    VALID_STATUSES = ('pending', 'approved', 'rejected')

    test_sessions = db.relationship('TestSession', backref='access_request', lazy=True)

    def to_dict(self):
        return {
            'id': self.id, 'full_name': self.full_name, 'email': self.email,
            'company_name': self.company_name, 'phone': self.phone,
            'purpose': self.purpose, 'status': self.status,
            'approved_by': self.approved_by, 'rejection_note': self.rejection_note,
            'has_token': bool(self.access_token),
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'created_at': self.created_at.isoformat(),
            'actioned_at': self.actioned_at.isoformat() if self.actioned_at else None,
        }


# ============================================================
# Section C — Industrial Testing Software
# ============================================================

class TestSession(db.Model):
    """One physical test run on a valve / component."""
    __tablename__ = 'test_sessions'

    id                = db.Column(db.Integer, primary_key=True)
    session_code      = db.Column(db.String(50), nullable=False, unique=True)
    operator_name     = db.Column(db.String(150), nullable=False)
    operator_email    = db.Column(db.String(150))
    access_request_id = db.Column(
        db.Integer, db.ForeignKey('testing_access_requests.id', ondelete='SET NULL'), nullable=True
    )
    # Device under test
    valve_id          = db.Column(db.String(100))
    valve_type        = db.Column(db.String(100))
    valve_size        = db.Column(db.String(50))
    client_name       = db.Column(db.String(200))
    job_number        = db.Column(db.String(100))
    # Test configuration
    test_type         = db.Column(db.String(50), nullable=False, default='standard')
    medium            = db.Column(db.String(50), nullable=False, default='water')
    target_pressure   = db.Column(db.Numeric(8, 2))
    target_duration   = db.Column(db.Integer)
    temperature_limit = db.Column(db.Numeric(5, 2))
    # Lifecycle
    status            = db.Column(db.String(20), nullable=False, default='setup')
    started_at        = db.Column(db.DateTime)
    ended_at          = db.Column(db.DateTime)
    duration_seconds  = db.Column(db.Integer)
    # Result
    result      = db.Column(db.String(20))
    notes       = db.Column(db.Text)
    reviewed_by = db.Column(db.String(150))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    VALID_STATUSES = ('setup', 'running', 'paused', 'completed', 'aborted')
    VALID_RESULTS  = ('passed', 'failed', 'inconclusive')
    VALID_TYPES    = ('standard', 'hydrostatic', 'pneumatic', 'leakage')
    VALID_MEDIUMS  = ('water', 'air', 'gas', 'oil')

    readings      = db.relationship(
        'TestReading', backref='session', lazy=True, cascade='all, delete-orphan'
    )
    result_record = db.relationship(
        'TestResult', backref='session', uselist=False, cascade='all, delete-orphan'
    )

    def _f(self, v):
        return float(v) if v is not None else None

    def to_dict(self):
        return {
            'id': self.id, 'session_code': self.session_code,
            'operator_name': self.operator_name, 'operator_email': self.operator_email,
            'valve_id': self.valve_id, 'valve_type': self.valve_type,
            'valve_size': self.valve_size, 'client_name': self.client_name,
            'job_number': self.job_number, 'test_type': self.test_type,
            'medium': self.medium,
            'target_pressure': self._f(self.target_pressure),
            'target_duration': self.target_duration,
            'temperature_limit': self._f(self.temperature_limit),
            'status': self.status, 'result': self.result, 'notes': self.notes,
            'reviewed_by': self.reviewed_by,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class TestReading(db.Model):
    """Time-series sensor readings captured during a test session."""
    __tablename__ = 'test_readings'

    id             = db.Column(db.BigInteger, primary_key=True)
    session_id     = db.Column(
        db.Integer, db.ForeignKey('test_sessions.id', ondelete='CASCADE'), nullable=False
    )
    recorded_at    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pressure_bar   = db.Column(db.Numeric(8, 3))
    temperature_c  = db.Column(db.Numeric(6, 2))
    flow_rate_lpm  = db.Column(db.Numeric(8, 3))
    leakage_ml_min = db.Column(db.Numeric(8, 3))
    rpm            = db.Column(db.Numeric(7, 2))
    pressure_alert = db.Column(db.String(10), default='ok')
    temp_alert     = db.Column(db.String(10), default='ok')
    leakage_alert  = db.Column(db.String(10), default='ok')

    def _f(self, v):
        return float(v) if v is not None else None

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
    """Aggregated result record created when a test session completes."""
    __tablename__ = 'test_results'

    id                    = db.Column(db.Integer, primary_key=True)
    session_id            = db.Column(
        db.Integer, db.ForeignKey('test_sessions.id', ondelete='CASCADE'),
        nullable=False, unique=True
    )
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

    def _f(self, v):
        return float(v) if v is not None else None

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
            'pressure_limit_bar': self._f(self.pressure_limit_bar),
            'leakage_limit_ml_min': self._f(self.leakage_limit_ml_min),
            'duration_achieved_sec': self.duration_achieved_sec,
            'ai_summary': self.ai_summary,
            'ai_anomalies': self.ai_anomalies or [],
            'ai_confidence': self._f(self.ai_confidence),
            'pdf_url': self.pdf_url, 'csv_url': self.csv_url,
            'engineer_signed_by': self.engineer_signed_by,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'created_at': self.created_at.isoformat(),
        }


class TestSettings(db.Model):
    """Single-row machine configuration for the testing software."""
    __tablename__ = 'test_settings'

    id                   = db.Column(db.Integer, primary_key=True, default=1)
    machine_id           = db.Column(db.String(50),  nullable=False, default='MACHINE-01')
    max_pressure_bar     = db.Column(db.Numeric(8, 2), nullable=False, default=250.0)
    min_pressure_bar     = db.Column(db.Numeric(8, 2), nullable=False, default=0.0)
    pressure_warning_pct = db.Column(db.Integer,      nullable=False, default=85)
    max_leakage_ml_min   = db.Column(db.Numeric(8, 3), nullable=False, default=5.0)
    leakage_warning_ml   = db.Column(db.Numeric(8, 3), nullable=False, default=2.0)
    max_temp_c           = db.Column(db.Numeric(6, 2), nullable=False, default=80.0)
    temp_warning_c       = db.Column(db.Numeric(6, 2), nullable=False, default=65.0)
    default_duration_sec = db.Column(db.Integer,      nullable=False, default=300)
    reading_interval_ms  = db.Column(db.Integer,      nullable=False, default=1000)
    ai_enabled           = db.Column(db.Boolean,      nullable=False, default=True)
    ai_model             = db.Column(db.String(100),  nullable=False, default='llama3')
    ai_sensitivity       = db.Column(db.String(20),   nullable=False, default='medium')
    last_calibrated_at   = db.Column(db.DateTime)
    calibrated_by        = db.Column(db.String(150))
    calibration_notes    = db.Column(db.Text)
    updated_at           = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls):
        """Always returns the single settings row, creating it if missing."""
        cfg = cls.query.get(1)
        if not cfg:
            cfg = cls(id=1)
            db.session.add(cfg)
            db.session.commit()
        return cfg

    def _f(self, v):
        return float(v) if v is not None else None

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
            'ai_enabled': self.ai_enabled, 'ai_model': self.ai_model,
            'ai_sensitivity': self.ai_sensitivity,
            'last_calibrated_at': self.last_calibrated_at.isoformat() if self.last_calibrated_at else None,
            'calibrated_by': self.calibrated_by,
            'calibration_notes': self.calibration_notes,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================
# Section D — Admin Intelligence & Audit
# ============================================================

class AIInsight(db.Model):
    """AI-generated operational insights shown in the admin panel."""
    __tablename__ = 'ai_insights'

    id           = db.Column(db.Integer, primary_key=True)
    insight_type = db.Column(db.String(50),  nullable=False)
    title        = db.Column(db.String(200), nullable=False)
    body         = db.Column(db.Text,        nullable=False)
    severity     = db.Column(db.String(20),  nullable=False, default='info')
    is_read      = db.Column(db.Boolean,     nullable=False, default=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at   = db.Column(db.DateTime)

    VALID_TYPES      = ('stock_alert', 'production_suggestion', 'test_failure_pattern', 'demand_forecast')
    VALID_SEVERITIES = ('info', 'warning', 'critical')

    def to_dict(self):
        return {
            'id': self.id, 'insight_type': self.insight_type,
            'title': self.title, 'body': self.body,
            'severity': self.severity, 'is_read': self.is_read,
            'generated_at': self.generated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }


class ActivityLog(db.Model):
    """Audit trail for all significant admin and system actions."""
    __tablename__ = 'activity_log'

    id          = db.Column(db.Integer,     primary_key=True)
    actor       = db.Column(db.String(150), nullable=False, default='system')
    action      = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id   = db.Column(db.Integer)
    description = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'actor': self.actor, 'action': self.action,
            'entity_type': self.entity_type, 'entity_id': self.entity_id,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
        }


def log_activity(action, entity_type=None, entity_id=None, description=None, actor='system'):
    """
    Convenience helper — write one ActivityLog row.
    Caller is responsible for db.session.commit().
    """
    db.session.add(ActivityLog(
        actor=actor, action=action,
        entity_type=entity_type, entity_id=entity_id,
        description=description,
    ))
