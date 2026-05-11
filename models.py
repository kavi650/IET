from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ============================================================
# EXISTING MODELS (unchanged)
# ============================================================

class User(db.Model):
    """Admin users table."""
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'email':      self.email,
            'created_at': self.created_at.isoformat()
        }


class Category(db.Model):
    """Product categories."""
    __tablename__ = 'categories'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon        = db.Column(db.String(50))
    products    = db.relationship('Product', backref='category', lazy=True)

    def to_dict(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'description': self.description,
            'icon':        self.icon
        }


class Product(db.Model):
    """Industrial products — extended with stock fields."""
    __tablename__ = 'products'

    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(200), nullable=False)
    category_id       = db.Column(db.Integer, db.ForeignKey('categories.id'))
    description       = db.Column(db.Text)
    working_principle = db.Column(db.Text)
    applications      = db.Column(db.Text)
    image_url         = db.Column(db.String(500))
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    # --- STORES: new inventory columns ---
    stock         = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)

    # Relationships
    specifications = db.relationship(
        'Specification', backref='product', lazy=True, cascade='all, delete-orphan'
    )
    stock_logs = db.relationship(
        'StockUsageLog', backref='product', lazy=True, cascade='all, delete-orphan'
    )

    @property
    def is_low_stock(self):
        """True when stock has fallen below the reorder level."""
        return self.stock < self.reorder_level

    def to_dict(self):
        return {
            'id':                self.id,
            'name':              self.name,
            'category_id':       self.category_id,
            'category_name':     self.category.name if self.category else None,
            'description':       self.description,
            'working_principle': self.working_principle,
            'applications':      self.applications,
            'image_url':         self.image_url,
            'stock':             self.stock,
            'reorder_level':     self.reorder_level,
            'is_low_stock':      self.is_low_stock,
            'specifications':    [s.to_dict() for s in self.specifications],
            'created_at':        self.created_at.isoformat()
        }

    def to_card_dict(self):
        """Lighter dict for product listing cards."""
        return {
            'id':           self.id,
            'name':         self.name,
            'category_id':  self.category_id,
            'category_name': self.category.name if self.category else None,
            'description':  (
                self.description[:150] + '...'
                if self.description and len(self.description) > 150
                else self.description
            ),
            'image_url':    self.image_url,
            'stock':        self.stock,
            'is_low_stock': self.is_low_stock
        }


class Specification(db.Model):
    """Product technical specifications (key-value pairs)."""
    __tablename__ = 'specifications'

    id         = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'))
    key        = db.Column(db.String(100), nullable=False)
    value      = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'key': self.key, 'value': self.value}


class Enquiry(db.Model):
    """Contact/enquiry submissions — extended with sales pipeline fields."""
    __tablename__ = 'enquiries'

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(100), nullable=False)
    email           = db.Column(db.String(150), nullable=False)
    company         = db.Column(db.String(200))
    message         = db.Column(db.Text, nullable=False)
    is_read         = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # --- SALES: new pipeline columns ---
    status          = db.Column(db.String(20), nullable=False, default='new')
    estimated_value = db.Column(db.Numeric(12, 2), default=0)
    phone           = db.Column(db.String(30))
    product_id      = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)

    # Relationship: one enquiry can spawn one production order (when status = 'won')
    production_orders = db.relationship('ProductionOrder', backref='enquiry', lazy=True)

    VALID_STATUSES = ('new', 'contacted', 'quotation', 'won', 'lost')

    STATUS_COLORS = {
        'new':       'blue',
        'contacted': 'orange',
        'quotation': 'purple',
        'won':       'green',
        'lost':      'red',
    }

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self.status, 'grey')

    def to_dict(self):
        return {
            'id':              self.id,
            'name':            self.name,
            'email':           self.email,
            'company':         self.company,
            'phone':           self.phone,
            'message':         self.message,
            'is_read':         self.is_read,
            'status':          self.status,
            'status_color':    self.status_color,
            'estimated_value': float(self.estimated_value) if self.estimated_value else 0,
            'product_id':      self.product_id,
            'created_at':      self.created_at.isoformat()
        }


class ChatbotLog(db.Model):
    """Chat conversation logs."""
    __tablename__ = 'chatbot_logs'

    id         = db.Column(db.Integer, primary_key=True)
    query      = db.Column(db.Text, nullable=False)
    response   = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'query':      self.query,
            'response':   self.response,
            'created_at': self.created_at.isoformat()
        }


# ============================================================
# NEW MODELS — Departments
# ============================================================

class ProductionOrder(db.Model):
    """Production orders — created from won sales enquiries."""
    __tablename__ = 'production_orders'

    id         = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
    enquiry_id = db.Column(db.Integer, db.ForeignKey('enquiries.id', ondelete='SET NULL'), nullable=True)
    quantity   = db.Column(db.Integer, nullable=False, default=1)
    start_date = db.Column(db.Date)
    due_date   = db.Column(db.Date)
    status     = db.Column(db.String(20), nullable=False, default='pending')
    progress   = db.Column(db.Integer, nullable=False, default=0)
    notes      = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    VALID_STATUSES = ('pending', 'in_progress', 'completed', 'cancelled')

    # Relationships
    product         = db.relationship('Product', backref='production_orders', lazy='select')
    assembly        = db.relationship('Assembly', backref='production_order', uselist=False, cascade='all, delete-orphan')
    electrical_test = db.relationship('ElectricalTest', backref='production_order', uselist=False, cascade='all, delete-orphan')

    @property
    def product_name(self):
        return self.product.name if self.product else 'N/A'

    def to_dict(self):
        return {
            'id':           self.id,
            'product_id':   self.product_id,
            'product_name': self.product_name,
            'enquiry_id':   self.enquiry_id,
            'quantity':     self.quantity,
            'start_date':   self.start_date.isoformat() if self.start_date else None,
            'due_date':     self.due_date.isoformat() if self.due_date else None,
            'status':       self.status,
            'progress':     self.progress,
            'notes':        self.notes,
            'created_at':   self.created_at.isoformat(),
            'updated_at':   self.updated_at.isoformat() if self.updated_at else None
        }


class Assembly(db.Model):
    """Assembly checklist linked to a production order."""
    __tablename__ = 'assembly'

    id            = db.Column(db.Integer, primary_key=True)
    production_id = db.Column(
        db.Integer,
        db.ForeignKey('production_orders.id', ondelete='CASCADE'),
        nullable=False,
        unique=True          # one checklist per order
    )
    checklist     = db.Column(db.JSON, nullable=False, default=list)
    # Format: [{"item": "Motor", "done": true}, {"item": "Pump", "done": false}]
    status        = db.Column(db.String(20), nullable=False, default='pending')
    progress      = db.Column(db.Integer, nullable=False, default=0)
    assigned_to   = db.Column(db.String(100))
    notes         = db.Column(db.Text)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    VALID_STATUSES = ('pending', 'in_progress', 'completed')

    def recalculate_progress(self):
        """Recalculate progress % from checklist and auto-update status."""
        if not self.checklist:
            self.progress = 0
            self.status = 'pending'
            return
        total = len(self.checklist)
        done  = sum(1 for item in self.checklist if item.get('done'))
        self.progress = int((done / total) * 100) if total else 0
        if self.progress == 0:
            self.status = 'pending'
        elif self.progress == 100:
            self.status = 'completed'
        else:
            self.status = 'in_progress'

    def to_dict(self):
        return {
            'id':            self.id,
            'production_id': self.production_id,
            'checklist':     self.checklist,
            'status':        self.status,
            'progress':      self.progress,
            'assigned_to':   self.assigned_to,
            'notes':         self.notes,
            'created_at':    self.created_at.isoformat(),
            'updated_at':    self.updated_at.isoformat() if self.updated_at else None
        }


class ElectricalTest(db.Model):
    """Electrical test results linked to a production order."""
    __tablename__ = 'electrical_tests'

    id            = db.Column(db.Integer, primary_key=True)
    production_id = db.Column(
        db.Integer,
        db.ForeignKey('production_orders.id', ondelete='CASCADE'),
        nullable=False,
        unique=True          # one test record per order
    )
    panel_type    = db.Column(db.String(100))
    plc_type      = db.Column(db.String(100))
    voltage       = db.Column(db.String(50))
    test_status   = db.Column(db.String(20), nullable=False, default='pending')
    remarks       = db.Column(db.Text)
    tested_by     = db.Column(db.String(100))
    test_date     = db.Column(db.Date)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    VALID_STATUSES = ('pending', 'passed', 'failed')

    def to_dict(self):
        return {
            'id':            self.id,
            'production_id': self.production_id,
            'panel_type':    self.panel_type,
            'plc_type':      self.plc_type,
            'voltage':       self.voltage,
            'test_status':   self.test_status,
            'remarks':       self.remarks,
            'tested_by':     self.tested_by,
            'test_date':     self.test_date.isoformat() if self.test_date else None,
            'created_at':    self.created_at.isoformat(),
            'updated_at':    self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================
# NEW MODELS — System
# ============================================================

class SiteConfig(db.Model):
    """Single-row site configuration (maintenance mode, message, etc.)."""
    __tablename__ = 'site_config'

    id                  = db.Column(db.Integer, primary_key=True, default=1)
    maintenance_mode    = db.Column(db.Boolean, nullable=False, default=False)
    maintenance_message = db.Column(
        db.Text,
        default='We are currently undergoing scheduled maintenance. Please check back soon.'
    )
    affected_pages      = db.Column(db.ARRAY(db.Text), default=list)
    # Empty list = site-wide; populated list = specific routes e.g. ['/products', '/contact']
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls):
        """Always returns the single config row, creating it if missing."""
        cfg = cls.query.get(1)
        if not cfg:
            cfg = cls(id=1)
            db.session.add(cfg)
            db.session.commit()
        return cfg

    def to_dict(self):
        return {
            'maintenance_mode':    self.maintenance_mode,
            'maintenance_message': self.maintenance_message,
            'affected_pages':      self.affected_pages or [],
            'updated_at':          self.updated_at.isoformat() if self.updated_at else None
        }


class StockUsageLog(db.Model):
    """Audit log for every stock add/reduce action on products."""
    __tablename__ = 'stock_usage_log'

    id           = db.Column(db.Integer, primary_key=True)
    product_id   = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False
    )
    change_qty   = db.Column(db.Integer, nullable=False)   # positive = added, negative = consumed
    reason       = db.Column(db.String(100))               # 'production', 'manual_add', 'manual_reduce'
    reference_id = db.Column(db.Integer)                   # optional: production_orders.id
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':           self.id,
            'product_id':   self.product_id,
            'product_name': self.product.name if self.product else None,
            'change_qty':   self.change_qty,
            'reason':       self.reason,
            'reference_id': self.reference_id,
            'created_at':   self.created_at.isoformat()
        }


# ============================================================
# V3 models — register all new tables with SQLAlchemy
# ============================================================
from models_v3 import (  # noqa: E402, F401
    Project, Download, Industry,
    TestingAccessRequest,
    TestSession, TestReading, TestResult, TestSettings,
    AIInsight, ActivityLog, log_activity,
)
