-- ============================================================
-- Teslead Equipments — Schema v2 (Additive Migration)
-- PostgreSQL
--
-- Run AFTER the original schema.sql is already applied.
-- This script only ADDS new columns and new tables.
-- It will NOT touch or drop existing data.
-- ============================================================


-- ============================================================
-- SECTION 1: STORES — Extend products table
-- ============================================================

-- Add inventory columns to existing products table
ALTER TABLE products
    ADD COLUMN IF NOT EXISTS stock         INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS reorder_level INTEGER NOT NULL DEFAULT 10;

-- Index for quick low-stock queries
CREATE INDEX IF NOT EXISTS idx_products_low_stock
    ON products (stock, reorder_level);


-- ============================================================
-- SECTION 2: SALES — Extend enquiries table
-- ============================================================

ALTER TABLE enquiries
    ADD COLUMN IF NOT EXISTS status          VARCHAR(20) NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'contacted', 'quotation', 'won', 'lost')),
    ADD COLUMN IF NOT EXISTS estimated_value NUMERIC(12, 2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS phone           VARCHAR(30),
    ADD COLUMN IF NOT EXISTS product_id      INTEGER REFERENCES products(id) ON DELETE SET NULL;

-- Index for pipeline/kanban queries
CREATE INDEX IF NOT EXISTS idx_enquiries_status ON enquiries(status);


-- ============================================================
-- SECTION 3: PRODUCTION — production_orders table
-- ============================================================

CREATE TABLE IF NOT EXISTS production_orders (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER REFERENCES products(id) ON DELETE SET NULL,
    enquiry_id  INTEGER REFERENCES enquiries(id) ON DELETE SET NULL,  -- traceability: which sale created this
    quantity    INTEGER NOT NULL DEFAULT 1,
    start_date  DATE,
    due_date    DATE,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    progress    INTEGER NOT NULL DEFAULT 0
        CHECK (progress BETWEEN 0 AND 100),
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prodorders_status  ON production_orders(status);
CREATE INDEX IF NOT EXISTS idx_prodorders_product ON production_orders(product_id);


-- ============================================================
-- SECTION 4: ASSEMBLY — assembly table
-- ============================================================

CREATE TABLE IF NOT EXISTS assembly (
    id            SERIAL PRIMARY KEY,
    production_id INTEGER NOT NULL REFERENCES production_orders(id) ON DELETE CASCADE,
    checklist     JSONB NOT NULL DEFAULT '[]',
    -- checklist format: [{"item": "Motor", "done": true}, {"item": "Pump", "done": false}]
    status        VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed')),
    progress      INTEGER NOT NULL DEFAULT 0
        CHECK (progress BETWEEN 0 AND 100),   -- auto-calculated from checklist
    assigned_to   VARCHAR(100),
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_assembly_production
    ON assembly(production_id);    -- one assembly record per production order

CREATE INDEX IF NOT EXISTS idx_assembly_status ON assembly(status);


-- ============================================================
-- SECTION 5: ELECTRICAL — electrical_tests table
-- ============================================================

CREATE TABLE IF NOT EXISTS electrical_tests (
    id            SERIAL PRIMARY KEY,
    production_id INTEGER NOT NULL REFERENCES production_orders(id) ON DELETE CASCADE,
    panel_type    VARCHAR(100),
    plc_type      VARCHAR(100),
    voltage       VARCHAR(50),
    test_status   VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (test_status IN ('pending', 'passed', 'failed')),
    remarks       TEXT,
    tested_by     VARCHAR(100),
    test_date     DATE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_electrical_production ON electrical_tests(production_id);
CREATE INDEX IF NOT EXISTS idx_electrical_status     ON electrical_tests(test_status);


-- ============================================================
-- SECTION 6: MAINTENANCE — site_config table
-- (replaces hard-coded maintenance toggle)
-- ============================================================

CREATE TABLE IF NOT EXISTS site_config (
    id                  SERIAL PRIMARY KEY,
    maintenance_mode    BOOLEAN NOT NULL DEFAULT FALSE,
    maintenance_message TEXT    DEFAULT 'We are currently undergoing scheduled maintenance. Please check back soon.',
    affected_pages      TEXT[]  DEFAULT ARRAY[]::TEXT[],
    -- e.g. ARRAY['/products', '/contact']  — empty = site-wide
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ensure exactly one config row always exists
INSERT INTO site_config (id, maintenance_mode)
    VALUES (1, FALSE)
    ON CONFLICT (id) DO NOTHING;


-- ============================================================
-- SECTION 7: REPORTS — stock_usage_log table
-- (lightweight audit trail for stock add/reduce actions)
-- ============================================================

CREATE TABLE IF NOT EXISTS stock_usage_log (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    change_qty  INTEGER NOT NULL,   -- positive = stock added, negative = stock consumed
    reason      VARCHAR(100),       -- e.g. 'production', 'manual_add', 'manual_reduce'
    reference_id INTEGER,           -- optional FK to production_orders.id
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stocklog_product ON stock_usage_log(product_id);
CREATE INDEX IF NOT EXISTS idx_stocklog_date    ON stock_usage_log(created_at);


-- ============================================================
-- HELPER: auto-update updated_at columns via trigger
-- ============================================================

CREATE OR REPLACE FUNCTION trg_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    -- production_orders
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_updated_at_production_orders'
    ) THEN
        CREATE TRIGGER set_updated_at_production_orders
        BEFORE UPDATE ON production_orders
        FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
    END IF;

    -- assembly
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_updated_at_assembly'
    ) THEN
        CREATE TRIGGER set_updated_at_assembly
        BEFORE UPDATE ON assembly
        FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
    END IF;

    -- electrical_tests
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_updated_at_electrical_tests'
    ) THEN
        CREATE TRIGGER set_updated_at_electrical_tests
        BEFORE UPDATE ON electrical_tests
        FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
    END IF;

    -- site_config
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_updated_at_site_config'
    ) THEN
        CREATE TRIGGER set_updated_at_site_config
        BEFORE UPDATE ON site_config
        FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
    END IF;
END;
$$;


-- ============================================================
-- END OF SCHEMA v2
-- ============================================================
