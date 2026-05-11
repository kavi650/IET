-- ============================================================
-- schema_v3.sql  — Testiny Platform v3  (Additive Only)
-- Run AFTER existing schema_v2.sql
-- All new tables. Existing tables are NOT modified here.
-- Use migrate_v3.py to apply safely.
-- ============================================================

-- ============================================================
-- SECTION A — PUBLIC WEBSITE EXTENSIONS
-- ============================================================

-- A1. Projects / Case Studies
CREATE TABLE IF NOT EXISTS projects (
    id           SERIAL PRIMARY KEY,
    title        VARCHAR(200)  NOT NULL,
    client_name  VARCHAR(200),
    industry     VARCHAR(100),              -- 'oil_gas', 'automobile', 'power_plant', 'manufacturing'
    problem      TEXT,
    solution     TEXT,
    result       TEXT,
    image_url    VARCHAR(500),
    is_published BOOLEAN       NOT NULL DEFAULT FALSE,
    sort_order   INTEGER       NOT NULL DEFAULT 0,
    created_at   TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP     NOT NULL DEFAULT NOW()
);

-- A2. Downloadable resources (brochures, datasheets, PDFs)
CREATE TABLE IF NOT EXISTS downloads (
    id           SERIAL PRIMARY KEY,
    title        VARCHAR(200)  NOT NULL,
    description  TEXT,
    category     VARCHAR(50)   NOT NULL DEFAULT 'brochure',  -- 'brochure', 'datasheet', 'technical', 'certificate'
    file_url     VARCHAR(500)  NOT NULL,
    file_size_kb INTEGER,
    is_published BOOLEAN       NOT NULL DEFAULT TRUE,
    download_count INTEGER     NOT NULL DEFAULT 0,
    created_at   TIMESTAMP     NOT NULL DEFAULT NOW()
);

-- A3. Industries served (managed from admin)
CREATE TABLE IF NOT EXISTS industries (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(100) NOT NULL UNIQUE,   -- 'oil-gas', 'automobile', etc.
    description TEXT,
    icon        VARCHAR(50),
    image_url   VARCHAR(500),
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ============================================================
-- SECTION B — TESTING ACCESS CONTROL
-- ============================================================

-- B1. Testing software access requests (from public users)
CREATE TABLE IF NOT EXISTS testing_access_requests (
    id              SERIAL PRIMARY KEY,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(150) NOT NULL,
    company_name    VARCHAR(200),
    phone           VARCHAR(30),
    purpose         TEXT,                        -- Why they need access
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
    approved_by     VARCHAR(100),                -- Admin name who actioned
    rejection_note  TEXT,                        -- Reason if rejected
    access_token    VARCHAR(64)  UNIQUE,         -- UUID token issued on approval
    token_expires_at TIMESTAMP,                  -- Token expiry (optional)
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    actioned_at     TIMESTAMP,                   -- When admin approved/rejected

    CONSTRAINT chk_access_status CHECK (status IN ('pending', 'approved', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_access_requests_status    ON testing_access_requests(status);
CREATE INDEX IF NOT EXISTS idx_access_requests_email     ON testing_access_requests(email);
CREATE INDEX IF NOT EXISTS idx_access_requests_token     ON testing_access_requests(access_token);

-- ============================================================
-- SECTION C — INDUSTRIAL TESTING SOFTWARE
-- ============================================================

-- C1. Test sessions (one session = one physical test run)
CREATE TABLE IF NOT EXISTS test_sessions (
    id              SERIAL PRIMARY KEY,
    session_code    VARCHAR(50)  NOT NULL UNIQUE,  -- e.g. 'TS-2026-001'
    operator_name   VARCHAR(150) NOT NULL,
    operator_email  VARCHAR(150),
    access_request_id INTEGER REFERENCES testing_access_requests(id) ON DELETE SET NULL,

    -- Device under test
    valve_id        VARCHAR(100),               -- Customer's valve serial / tag number
    valve_type      VARCHAR(100),               -- 'ball', 'gate', 'butterfly', 'check', etc.
    valve_size      VARCHAR(50),                -- DN50, 2", etc.
    client_name     VARCHAR(200),
    job_number      VARCHAR(100),

    -- Test configuration
    test_type       VARCHAR(50)  NOT NULL DEFAULT 'standard',  -- 'standard', 'hydrostatic', 'pneumatic', 'leakage'
    medium          VARCHAR(50)  NOT NULL DEFAULT 'water',     -- 'water', 'air', 'gas', 'oil'
    target_pressure NUMERIC(8,2),              -- in bar
    target_duration INTEGER,                   -- in seconds
    temperature_limit NUMERIC(5,2),            -- in °C

    -- Session lifecycle
    status          VARCHAR(20)  NOT NULL DEFAULT 'setup',  -- setup | running | paused | completed | aborted
    started_at      TIMESTAMP,
    ended_at        TIMESTAMP,
    duration_seconds INTEGER,

    -- Final outcome
    result          VARCHAR(20),               -- passed | failed | inconclusive
    notes           TEXT,
    reviewed_by     VARCHAR(150),
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_session_status CHECK (status IN ('setup', 'running', 'paused', 'completed', 'aborted')),
    CONSTRAINT chk_session_result CHECK (result IN ('passed', 'failed', 'inconclusive') OR result IS NULL)
);

CREATE INDEX IF NOT EXISTS idx_test_sessions_status     ON test_sessions(status);
CREATE INDEX IF NOT EXISTS idx_test_sessions_result     ON test_sessions(result);
CREATE INDEX IF NOT EXISTS idx_test_sessions_created_at ON test_sessions(created_at);

-- C2. Live sensor readings (time-series data per session)
CREATE TABLE IF NOT EXISTS test_readings (
    id              BIGSERIAL PRIMARY KEY,
    session_id      INTEGER      NOT NULL REFERENCES test_sessions(id) ON DELETE CASCADE,
    recorded_at     TIMESTAMP    NOT NULL DEFAULT NOW(),

    -- Sensor values
    pressure_bar    NUMERIC(8,3),              -- Current pressure in bar
    temperature_c   NUMERIC(6,2),              -- Temperature in °C
    flow_rate_lpm   NUMERIC(8,3),              -- Flow rate L/min
    leakage_ml_min  NUMERIC(8,3),              -- Leakage in mL/min
    rpm             NUMERIC(7,2),              -- RPM if applicable

    -- Alert flags (set by system)
    pressure_alert  VARCHAR(10)  DEFAULT 'ok',  -- ok | warning | critical
    temp_alert      VARCHAR(10)  DEFAULT 'ok',
    leakage_alert   VARCHAR(10)  DEFAULT 'ok',

    CONSTRAINT chk_pressure_alert  CHECK (pressure_alert IN ('ok', 'warning', 'critical')),
    CONSTRAINT chk_temp_alert      CHECK (temp_alert     IN ('ok', 'warning', 'critical')),
    CONSTRAINT chk_leakage_alert   CHECK (leakage_alert  IN ('ok', 'warning', 'critical'))
);

-- Partial index: only index recent/active session readings
CREATE INDEX IF NOT EXISTS idx_test_readings_session_time
    ON test_readings(session_id, recorded_at DESC);

-- C3. Test results (summary record after session completes)
CREATE TABLE IF NOT EXISTS test_results (
    id                    SERIAL PRIMARY KEY,
    session_id            INTEGER      NOT NULL UNIQUE REFERENCES test_sessions(id) ON DELETE CASCADE,

    -- Peak readings
    max_pressure_bar      NUMERIC(8,3),
    min_pressure_bar      NUMERIC(8,3),
    avg_pressure_bar      NUMERIC(8,3),
    max_temperature_c     NUMERIC(6,2),
    avg_flow_rate_lpm     NUMERIC(8,3),
    max_leakage_ml_min    NUMERIC(8,3),

    -- Test compliance
    pressure_hold_ok      BOOLEAN,              -- Did pressure hold for target duration?
    leakage_within_limit  BOOLEAN,
    temperature_ok        BOOLEAN,

    -- Limits used (snapshotted at test time)
    pressure_limit_bar    NUMERIC(8,3),
    leakage_limit_ml_min  NUMERIC(8,3),
    duration_achieved_sec INTEGER,

    -- AI analysis
    ai_summary            TEXT,                 -- AI-generated plain-English summary
    ai_anomalies          JSONB,                -- [{type, severity, description, recommendation}]
    ai_confidence         NUMERIC(4,2),         -- 0.00–1.00

    -- Report
    pdf_url               VARCHAR(500),         -- Generated PDF path
    csv_url               VARCHAR(500),
    engineer_signed_by    VARCHAR(150),
    signed_at             TIMESTAMP,

    created_at            TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- C4. Testing software settings (per-machine configuration)
CREATE TABLE IF NOT EXISTS test_settings (
    id                    SERIAL PRIMARY KEY DEFAULT 1,
    machine_id            VARCHAR(50)  NOT NULL DEFAULT 'MACHINE-01',

    -- Pressure limits
    max_pressure_bar      NUMERIC(8,2) NOT NULL DEFAULT 250.0,
    min_pressure_bar      NUMERIC(8,2) NOT NULL DEFAULT 0.0,
    pressure_warning_pct  INTEGER      NOT NULL DEFAULT 85,  -- % of max before warning

    -- Leakage tolerance
    max_leakage_ml_min    NUMERIC(8,3) NOT NULL DEFAULT 5.0,
    leakage_warning_ml    NUMERIC(8,3) NOT NULL DEFAULT 2.0,

    -- Temperature
    max_temp_c            NUMERIC(6,2) NOT NULL DEFAULT 80.0,
    temp_warning_c        NUMERIC(6,2) NOT NULL DEFAULT 65.0,

    -- Default test config
    default_duration_sec  INTEGER      NOT NULL DEFAULT 300,  -- 5 minutes
    reading_interval_ms   INTEGER      NOT NULL DEFAULT 1000,  -- 1 second

    -- AI config
    ai_enabled            BOOLEAN      NOT NULL DEFAULT TRUE,
    ai_model              VARCHAR(100) NOT NULL DEFAULT 'llama3',
    ai_sensitivity        VARCHAR(20)  NOT NULL DEFAULT 'medium',  -- low | medium | high

    -- Calibration
    last_calibrated_at    TIMESTAMP,
    calibrated_by         VARCHAR(150),
    calibration_notes     TEXT,

    updated_at            TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_ai_sensitivity CHECK (ai_sensitivity IN ('low', 'medium', 'high'))
);

-- Ensure single settings row
INSERT INTO test_settings (id, machine_id)
VALUES (1, 'MACHINE-01')
ON CONFLICT (id) DO NOTHING;

-- C5. AI Insights (admin-side, generated periodically or on-demand)
CREATE TABLE IF NOT EXISTS ai_insights (
    id           SERIAL PRIMARY KEY,
    insight_type VARCHAR(50)  NOT NULL,   -- 'stock_alert', 'production_suggestion', 'test_failure_pattern', 'demand_forecast'
    title        VARCHAR(200) NOT NULL,
    body         TEXT         NOT NULL,
    severity     VARCHAR(20)  NOT NULL DEFAULT 'info',  -- 'info', 'warning', 'critical'
    is_read      BOOLEAN      NOT NULL DEFAULT FALSE,
    generated_at TIMESTAMP    NOT NULL DEFAULT NOW(),
    expires_at   TIMESTAMP,

    CONSTRAINT chk_severity CHECK (severity IN ('info', 'warning', 'critical'))
);

CREATE INDEX IF NOT EXISTS idx_ai_insights_unread ON ai_insights(is_read, generated_at DESC);

-- C6. Activity log (audit trail for admin panel actions)
CREATE TABLE IF NOT EXISTS activity_log (
    id           SERIAL PRIMARY KEY,
    actor        VARCHAR(150) NOT NULL DEFAULT 'system',   -- admin name or 'system'
    action       VARCHAR(100) NOT NULL,                    -- 'created_order', 'approved_access', etc.
    entity_type  VARCHAR(50),                              -- 'production_order', 'test_session', etc.
    entity_id    INTEGER,
    description  TEXT,
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_log_created ON activity_log(created_at DESC);

-- ============================================================
-- SECTION D — SITE CONFIG EXTENSIONS
-- (Existing site_config table gets new columns via migrate_v3.py)
-- Listed here for documentation:
--   ALTER TABLE site_config ADD COLUMN company_name     VARCHAR(200) DEFAULT 'Testiny Equipments';
--   ALTER TABLE site_config ADD COLUMN company_tagline  TEXT;
--   ALTER TABLE site_config ADD COLUMN company_email    VARCHAR(150);
--   ALTER TABLE site_config ADD COLUMN company_phone    VARCHAR(50);
--   ALTER TABLE site_config ADD COLUMN company_address  TEXT;
--   ALTER TABLE site_config ADD COLUMN social_linkedin  VARCHAR(300);
--   ALTER TABLE site_config ADD COLUMN social_instagram VARCHAR(300);
--   ALTER TABLE site_config ADD COLUMN hero_announcement TEXT;
-- ============================================================

-- ============================================================
-- SECTION E — SEED DATA (Industries)
-- ============================================================

INSERT INTO industries (name, slug, description, icon, sort_order) VALUES
    ('Oil & Gas',        'oil-gas',       'Valve testing for upstream and downstream oil & gas operations including high-pressure pipeline valves.', 'fa-oil-can',       1),
    ('Automobile',       'automobile',    'Hydraulic and pneumatic testing rigs for automotive component manufacturers and assembly lines.',          'fa-car',           2),
    ('Power Plants',     'power-plants',  'High-temperature and high-pressure valve testing for thermal, nuclear, and renewable power generation.',  'fa-bolt',          3),
    ('Manufacturing',    'manufacturing', 'Industrial valve and actuator testing for general manufacturing, process industries, and OEMs.',          'fa-industry',      4),
    ('Water & Utilities','water',         'Leakage and pressure testing for municipal water supply, treatment plants and utility networks.',          'fa-droplet',       5),
    ('Aerospace',        'aerospace',     'Precision testing for lightweight high-performance valves used in aerospace and defence applications.',    'fa-plane',         6)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================
-- END OF schema_v3.sql
-- ============================================================
