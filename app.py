"""
Teslead Equipments - Flask Application
Refactored to use Blueprints for modular department structure.
All original routes are preserved; new department routes added via blueprints.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from models import (
    db, Category, Product, Specification,
    Enquiry, ChatbotLog, User,
    ProductionOrder, Assembly, ElectricalTest,
    SiteConfig, StockUsageLog
)
from config import Config

# Import v3 models so their tables are registered with SQLAlchemy
import models_v3  # noqa: F401

# ── Blueprints ────────────────────────────────────────────────
from blueprints.main           import main_bp
from blueprints.admin          import admin_bp
from blueprints.stores         import stores_bp
from blueprints.sales          import sales_bp
from blueprints.production     import production_bp
from blueprints.assembly       import assembly_bp
from blueprints.electrical     import electrical_bp
# v3
from blueprints.public_v3      import public_v3_bp
from blueprints.access         import access_bp
from blueprints.testing_admin  import testing_admin_bp
from blueprints.ai_admin       import ai_admin_bp
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def home():
    return render_template("index.html")

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    CORS(app)
    db.init_app(app)

    # ── Register blueprints ───────────────────────────────────
    app.register_blueprint(main_bp)           # /
    app.register_blueprint(admin_bp)          # /api/admin/*
    app.register_blueprint(stores_bp)         # /api/stores/*
    app.register_blueprint(sales_bp)          # /api/sales/*
    app.register_blueprint(production_bp)     # /api/production/*
    app.register_blueprint(assembly_bp)       # /api/assembly/*
    app.register_blueprint(electrical_bp)     # /api/electrical/*
    # v3
    app.register_blueprint(public_v3_bp)      # /process /projects /industries /downloads /testing-access
    app.register_blueprint(access_bp)         # /api/access/*
    app.register_blueprint(testing_admin_bp)  # /api/admin/access-requests test-sessions ai-insights activity
    app.register_blueprint(ai_admin_bp)       # /api/admin/ai/*

    # ── Global error handlers ─────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    return app


# ============================================================
# DATABASE INITIALISATION + SEED
# ============================================================

def init_db(app):
    """Create tables and seed initial data if the DB is empty."""
    with app.app_context():
        db.create_all()

        # ── Ensure site_config singleton exists ────────────────
        SiteConfig.get()

        # ── Seed categories if none exist ──────────────────────
        if Category.query.count() == 0:
            categories = [
                Category(name='Test Equipment',
                         description='Precision testing systems for industrial applications.',
                         icon='fa-flask'),
                Category(name='Hydraulic Systems',
                         description='Complete hydraulic solutions including power packs and cylinders.',
                         icon='fa-cogs'),
                Category(name='Pneumatic Systems',
                         description='Air-powered control systems and components.',
                         icon='fa-wind'),
                Category(name='Special Machines',
                         description='Custom-engineered industrial machines.',
                         icon='fa-industry'),
            ]
            db.session.add_all(categories)
            db.session.commit()

            # ── Seed products ──────────────────────────────────
            products_data = [
                {
                    'name': 'Pump Test Rig', 'cat': 1,
                    'desc': 'Advanced pump test rig for comprehensive performance evaluation of centrifugal, gear, vane, and piston pumps.',
                    'wp':   'Drives the pump under test via variable speed motor while measuring flow, pressure, torque, and power.',
                    'apps': 'Pump manufacturers, Oil & gas, Automotive, Power plants, Water treatment.',
                    'img':  '/static/images/pump_test_rig.jpg',
                    'specs': [
                        ('Flow Range', '0.5 - 5000 LPM'), ('Pressure Range', '0 - 500 bar'),
                        ('Drive Motor', '1 HP - 200 HP'), ('Accuracy', '±0.5% FS'),
                        ('Data Acquisition', 'PLC + HMI'), ('Test Medium', 'Water / Oil'),
                        ('Power Supply', '415V AC, 50Hz, 3-Phase')
                    ]
                },
                {
                    'name': 'Valve Test Bench', 'cat': 1,
                    'desc': 'High-precision valve test bench for safety, control, gate, and check valves.',
                    'wp':   'High-pressure hydraulic unit generates test pressures up to 1000 bar with automated PLC control.',
                    'apps': 'Valve manufacturers, Oil & gas refineries, Power plants, Chemical processing.',
                    'img':  '/static/images/valve_test_bench.jpg',
                    'specs': [
                        ('Test Pressure', 'Up to 1000 bar'), ('Pneumatic Test', 'Up to 50 bar'),
                        ('Valve Size', 'DN15 - DN600'), ('Standards', 'API 598, ISO 5208'),
                        ('Clamping', 'Hydraulic universal'), ('Reporting', 'Digital certificates')
                    ]
                },
                {
                    'name': 'Pressure Testing System', 'cat': 1,
                    'desc': 'Industrial pressure testing up to 2000 bar for vessels, pipelines, and fittings.',
                    'wp':   'Air-driven or electric-driven intensifiers with automated hold and decay monitoring.',
                    'apps': 'Pressure vessel mfg, Pipeline testing, Aerospace, Defense.',
                    'img':  '/static/images/pressure_testing.jpg',
                    'specs': [
                        ('Max Pressure', '2000 bar'), ('Accuracy', '±0.25% FS'),
                        ('Standards', 'ASME, EN, API'), ('Chart Recording', 'Digital + graph')
                    ]
                },
                {
                    'name': 'Hydraulic Power Pack', 'cat': 2,
                    'desc': 'Custom hydraulic power packs from 1 HP to 500 HP with variable pumps and integrated cooling.',
                    'wp':   'Electric motor drives hydraulic pump; fluid routed through valve manifold to actuators.',
                    'apps': 'Machine tools, Steel mills, Marine, Injection molding, Automation.',
                    'img':  '/static/images/hydraulic_power_pack.jpg',
                    'specs': [
                        ('Power Range', '1 HP - 500 HP'), ('Pressure', 'Up to 350 bar'),
                        ('Pump Type', 'Gear / Vane / Piston'), ('Reservoir', '10L - 5000L')
                    ]
                },
                {
                    'name': 'Hydraulic Cylinders', 'cat': 2,
                    'desc': 'Precision cylinders in tie-rod, welded, and telescopic types.',
                    'wp':   'Pressurized fluid acts on piston face creating linear force. Double-acting for both directions.',
                    'apps': 'Press manufacturing, Construction, Agriculture, Marine, Industrial lifting.',
                    'img':  '/static/images/hydraulic_cylinders.jpg',
                    'specs': [
                        ('Bore', '25mm - 500mm'), ('Stroke', 'Up to 6000mm'),
                        ('Pressure', 'Up to 350 bar'), ('Standards', 'ISO 6020/6022')
                    ]
                },
                {
                    'name': 'Hydraulic Pressure Boosters', 'cat': 2,
                    'desc': 'Pressure boosters amplifying system pressure by 2:1 to 10:1. No external power needed.',
                    'wp':   'Differential area pistons amplify pressure by area ratio.',
                    'apps': 'CNC clamping, Hydroforming, Pressure testing, Emergency systems.',
                    'img':  '/static/images/hydraulic_boosters.jpg',
                    'specs': [
                        ('Boost Ratio', '2:1 to 10:1'), ('Input', '50 - 250 bar'),
                        ('Output', 'Up to 2500 bar')
                    ]
                },
                {
                    'name': 'Pneumatic Control Systems', 'cat': 3,
                    'desc': 'Complete pneumatic control with precision regulators, directional valves, and FRL units.',
                    'wp':   'Compressed air controlled through solenoid/pilot valves to actuators.',
                    'apps': 'Packaging, Food & beverage, Pharma, Textile, Automotive assembly.',
                    'img':  '/static/images/pneumatic_control.jpg',
                    'specs': [
                        ('Pressure', '0 - 10 bar'), ('Valve Types', '3/2, 5/2, 5/3'),
                        ('Response', '< 25ms'), ('IP Rating', 'IP65 / IP67')
                    ]
                },
                {
                    'name': 'Air Preparation Units', 'cat': 3,
                    'desc': 'Industrial FRL units with staged filtration and IoT monitoring.',
                    'wp':   'Filters remove particles; regulators maintain pressure; lubricators inject oil mist.',
                    'apps': 'All pneumatic systems, Process industries, Paint spray.',
                    'img':  '/static/images/air_preparation.jpg',
                    'specs': [
                        ('Filter Grade', '5μm to 0.01μm'), ('Pressure', '0.5 - 10 bar'),
                        ('Flow', '500 - 15,000 Nl/min')
                    ]
                },
                {
                    'name': 'Custom SPM Machines', 'cat': 4,
                    'desc': 'Special Purpose Machines custom-designed for specific industrial operations.',
                    'wp':   'Engineered from scratch: process analysis, 3D modeling, FEA, PLC + HMI.',
                    'apps': 'Automotive, Aerospace, Defense, R&D labs, Assembly automation.',
                    'img':  '/static/images/custom_spm.jpg',
                    'specs': [
                        ('Design', 'Custom-engineered'), ('Automation', 'PLC + HMI'),
                        ('Warranty', '12 months + AMC')
                    ]
                },
                {
                    'name': 'Industrial Flushing Rigs', 'cat': 4,
                    'desc': 'High-velocity oil flushing rigs per NAS 1638 / ISO 4406.',
                    'wp':   'Turbulent oil flow through dual-stage filtration with online particle counting.',
                    'apps': 'Steel plants, Oil & gas, Power plants, Marine, Maintenance.',
                    'img':  '/static/images/flushing_rig.jpg',
                    'specs': [
                        ('Flow', '50 - 1000 LPM'), ('Filtration', '10μm + 3μm'),
                        ('Standards', 'NAS 1638, ISO 4406')
                    ]
                },
            ]

            for pdata in products_data:
                product = Product(
                    name              = pdata['name'],
                    category_id       = pdata['cat'],
                    description       = pdata['desc'],
                    working_principle = pdata['wp'],
                    applications      = pdata['apps'],
                    image_url         = pdata['img'],
                    stock             = 0,
                    reorder_level     = 10
                )
                db.session.add(product)
                db.session.flush()

                for key, value in pdata['specs']:
                    db.session.add(Specification(product_id=product.id, key=key, value=value))

            db.session.commit()
            print('✅ Database seeded successfully!')


# ============================================================
# ENTRY POINT
# ============================================================

app = create_app()

if __name__ == '__main__':
    init_db(app)
    app.run(debug=True, port=5000)
