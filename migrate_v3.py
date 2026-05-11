"""
migrate_v3.py  — Safe additive migration for platform v3
Run ONCE after schema_v2 is already applied.
Creates new tables and adds new columns to site_config.
Does NOT modify or drop any existing tables.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

# Import v3 models so SQLAlchemy knows about the new tables.
# NOTE: also add the following line to the BOTTOM of models.py:
#
#   from models_v3 import (
#       Project, Download, Industry, TestingAccessRequest,
#       TestSession, TestReading, TestResult, TestSettings,
#       AIInsight, ActivityLog, log_activity,
#   )
#
import models_v3  # noqa: F401


def run():
    with app.app_context():
        from sqlalchemy import text, inspect

        inspector = inspect(db.engine)
        existing  = inspector.get_table_names()

        print("── Testiny Platform v3 Migration ──────────────────────")

        # ── 1. Create new tables via SQLAlchemy ────────────────────
        new_tables = [
            'projects', 'downloads', 'industries',
            'testing_access_requests',
            'test_sessions', 'test_readings', 'test_results', 'test_settings',
            'ai_insights', 'activity_log',
        ]

        db.create_all()   # Safe: only creates missing tables, never drops

        for t in new_tables:
            status = '✓ created' if t not in existing else '· already exists'
            print(f"  {status:18}  {t}")

        # ── 2. Add new columns to site_config ─────────────────────
        new_site_config_cols = [
            ("company_name",     "VARCHAR(200) DEFAULT 'Testiny Equipments'"),
            ("company_tagline",  "TEXT"),
            ("company_email",    "VARCHAR(150)"),
            ("company_phone",    "VARCHAR(50)"),
            ("company_address",  "TEXT"),
            ("social_linkedin",  "VARCHAR(300)"),
            ("social_instagram", "VARCHAR(300)"),
            ("hero_announcement","TEXT"),
        ]

        if 'site_config' in existing:
            existing_cols = {c['name'] for c in inspector.get_columns('site_config')}
            for col_name, col_def in new_site_config_cols:
                if col_name not in existing_cols:
                    sql = f"ALTER TABLE site_config ADD COLUMN {col_name} {col_def}"
                    db.session.execute(text(sql))
                    print(f"  ✓ added column    site_config.{col_name}")
                else:
                    print(f"  · already exists  site_config.{col_name}")

        # ── 3. Seed test_settings singleton row ────────────────────
        result = db.session.execute(text("SELECT id FROM test_settings WHERE id=1")).fetchone()
        if not result:
            db.session.execute(text("""
                INSERT INTO test_settings (
                    id, machine_id,
                    max_pressure_bar, min_pressure_bar, pressure_warning_pct,
                    max_leakage_ml_min, leakage_warning_ml,
                    max_temp_c, temp_warning_c,
                    default_duration_sec, reading_interval_ms,
                    ai_enabled, ai_model, ai_sensitivity
                ) VALUES (
                    1, 'MACHINE-01',
                    250.0, 0.0, 85,
                    5.0, 2.0,
                    80.0, 65.0,
                    300, 1000,
                    TRUE, 'llama3', 'medium'
                )
            """))
            print("  ✓ seeded           test_settings (id=1)")
        else:
            print("  · already exists   test_settings (id=1)")

        # ── 4. Seed industries (6 rows) ────────────────────────────
        industries_seed = [
            ('Oil & Gas',         'oil-gas',       'Valve testing for upstream and downstream oil & gas operations.',                         'fa-oil-can',    1),
            ('Automobile',        'automobile',    'Hydraulic and pneumatic testing for automotive manufacturers and assembly lines.',         'fa-car',        2),
            ('Power Plants',      'power-plants',  'High-temperature and pressure valve testing for thermal and renewable power generation.',  'fa-bolt',       3),
            ('Manufacturing',     'manufacturing', 'Industrial valve and actuator testing for process industries and OEMs.',                   'fa-industry',   4),
            ('Water & Utilities', 'water',         'Leakage and pressure testing for municipal water supply and treatment plants.',            'fa-droplet',    5),
            ('Aerospace',         'aerospace',     'Precision testing for lightweight high-performance valves in aerospace applications.',     'fa-plane',      6),
        ]

        for name, slug, desc, icon, order in industries_seed:
            exists = db.session.execute(
                text("SELECT id FROM industries WHERE slug=:s"), {'s': slug}
            ).fetchone()
            if not exists:
                db.session.execute(text(
                    "INSERT INTO industries (name, slug, description, icon, sort_order, is_active) "
                    "VALUES (:n, :s, :d, :i, :o, TRUE)"
                ), {'n': name, 's': slug, 'd': desc, 'i': icon, 'o': order})
                print(f"  ✓ seeded           industries '{name}'")
            else:
                print(f"  · already exists   industries '{name}'")

        db.session.commit()
        print("\n✅ v3 migration complete.\n")
        print("NEXT STEP → add this import to the bottom of models.py:")
        print("  from models_v3 import (")
        print("      Project, Download, Industry, TestingAccessRequest,")
        print("      TestSession, TestReading, TestResult, TestSettings,")
        print("      AIInsight, ActivityLog, log_activity,")
        print("  )")


if __name__ == '__main__':
    run()
