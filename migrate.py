"""
migrate.py — Complete database migration for Teslead v2
Run ONCE: python migrate.py

Safely adds ALL missing columns to both old and new tables.
Every ALTER TABLE is guarded by an existence check — safe to re-run.
"""

import sys
from sqlalchemy import text
from app import app, db
from models import SiteConfig


def col_exists(conn, table, column):
    r = conn.execute(text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name=:t AND column_name=:c"
    ), {"t": table, "c": column}).fetchone()
    return r is not None


def table_exists(conn, table):
    r = conn.execute(text(
        "SELECT 1 FROM information_schema.tables WHERE table_name=:t"
    ), {"t": table}).fetchone()
    return r is not None


def add_col(conn, table, column, definition, done):
    if not col_exists(conn, table, column):
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
        conn.commit()
        print(f"  ✅ {table}.{column} added")
        done.append(f"{table}.{column}")
    else:
        print(f"  ⏭  {table}.{column} already exists")


def run():
    with app.app_context():
        done = []
        print("=" * 58)
        print("  Teslead v2 — Full Database Migration")
        print("=" * 58)

        with db.engine.connect() as conn:

            # ── 1. products ──────────────────────────────────────────
            print("\n[products]")
            add_col(conn, 'products', 'stock',         'INTEGER NOT NULL DEFAULT 0',  done)
            add_col(conn, 'products', 'reorder_level', 'INTEGER NOT NULL DEFAULT 10', done)

            # ── 2. enquiries ─────────────────────────────────────────
            print("\n[enquiries]")
            add_col(conn, 'enquiries', 'status',
                    "VARCHAR(20) NOT NULL DEFAULT 'new'", done)
            add_col(conn, 'enquiries', 'estimated_value',
                    'NUMERIC(12,2) DEFAULT 0', done)
            add_col(conn, 'enquiries', 'phone',
                    'VARCHAR(30)', done)
            add_col(conn, 'enquiries', 'product_id',
                    'INTEGER REFERENCES products(id) ON DELETE SET NULL', done)

            # ── 3. production_orders (may exist from earlier create_all) ──
            if table_exists(conn, 'production_orders'):
                print("\n[production_orders]")
                add_col(conn, 'production_orders', 'enquiry_id',
                        'INTEGER REFERENCES enquiries(id) ON DELETE SET NULL', done)
                add_col(conn, 'production_orders', 'progress',
                        'INTEGER NOT NULL DEFAULT 0', done)
                add_col(conn, 'production_orders', 'notes',
                        'TEXT', done)
                add_col(conn, 'production_orders', 'start_date',
                        'DATE', done)
                add_col(conn, 'production_orders', 'due_date',
                        'DATE', done)
                add_col(conn, 'production_orders', 'updated_at',
                        'TIMESTAMP DEFAULT NOW()', done)

            # ── 4. assembly ──────────────────────────────────────────
            if table_exists(conn, 'assembly'):
                print("\n[assembly]")
                add_col(conn, 'assembly', 'progress',
                        'INTEGER NOT NULL DEFAULT 0', done)
                add_col(conn, 'assembly', 'assigned_to',
                        'VARCHAR(100)', done)
                add_col(conn, 'assembly', 'notes',
                        'TEXT', done)
                add_col(conn, 'assembly', 'created_at',
                        'TIMESTAMP DEFAULT NOW()', done)
                add_col(conn, 'assembly', 'updated_at',
                        'TIMESTAMP DEFAULT NOW()', done)

            # ── 5. electrical_tests ──────────────────────────────────
            if table_exists(conn, 'electrical_tests'):
                print("\n[electrical_tests]")
                add_col(conn, 'electrical_tests', 'tested_by',
                        'VARCHAR(100)', done)
                add_col(conn, 'electrical_tests', 'test_date',
                        'DATE', done)
                add_col(conn, 'electrical_tests', 'created_at',
                        'TIMESTAMP DEFAULT NOW()', done)
                add_col(conn, 'electrical_tests', 'updated_at',
                        'TIMESTAMP DEFAULT NOW()', done)

        # ── 6. Create any still-missing tables ───────────────────────
        print("\nCreating any missing tables…")
        db.create_all()
        print("  ✅ db.create_all() done")

        # ── 7. Seed site_config singleton ────────────────────────────
        cfg = SiteConfig.get()
        print(f"  ✅ site_config row ready (maintenance={cfg.maintenance_mode})")

        print("\n" + "=" * 58)
        if done:
            print(f"  {len(done)} column(s) added. Restart Flask now.")
        else:
            print("  Nothing to migrate — schema is already up to date.")
        print("=" * 58)


if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
