-- ============================================================
-- DeepGuard Database Schema — MySQL 8
-- Single source of truth; matches SQLAlchemy ORM models exactly
-- ============================================================

CREATE DATABASE IF NOT EXISTS deepguard
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE deepguard;

-- ---------- Users ----------
CREATE TABLE users (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    full_name       VARCHAR(150)    NOT NULL,
    role            ENUM('admin', 'analyst', 'viewer') NOT NULL DEFAULT 'viewer',
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    last_login_at   DATETIME        NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX uq_users_email (email)
) ENGINE=InnoDB;

-- ---------- Customers ----------
CREATE TABLE customers (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_code   VARCHAR(50)     NOT NULL,
    name            VARCHAR(200)    NOT NULL,
    address         TEXT            NULL,
    region          VARCHAR(100)    NOT NULL,
    city            VARCHAR(100)    NULL,
    account_status  ENUM('active', 'suspended', 'closed') NOT NULL DEFAULT 'active',
    connection_type ENUM('residential', 'commercial', 'industrial') NOT NULL DEFAULT 'residential',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX uq_customers_code (customer_code),
    INDEX idx_customers_region (region),
    INDEX idx_customers_status (account_status)
) ENGINE=InnoDB;

-- ---------- Meters ----------
CREATE TABLE meters (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id     INT UNSIGNED    NOT NULL,
    meter_number    VARCHAR(50)     NOT NULL,
    meter_type      ENUM('smart', 'digital', 'analog') NOT NULL DEFAULT 'smart',
    install_date    DATE            NULL,
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX uq_meters_number (meter_number),
    INDEX idx_meters_customer (customer_id),

    CONSTRAINT fk_meters_customer
        FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------- Meter Readings (Time-Series) ----------
CREATE TABLE meter_readings (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    meter_id        INT UNSIGNED    NOT NULL,
    customer_id     INT UNSIGNED    NOT NULL,
    timestamp       DATETIME        NOT NULL,
    consumption_kwh DECIMAL(12,4)   NOT NULL,
    voltage         DECIMAL(8,2)    NULL,
    current_amps    DECIMAL(8,2)    NULL,
    power_factor    DECIMAL(5,4)    NULL,
    quality_flag    ENUM('valid', 'estimated', 'missing', 'suspect') NOT NULL DEFAULT 'valid',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_readings_customer_ts (customer_id, timestamp),
    INDEX idx_readings_meter_ts (meter_id, timestamp),
    INDEX idx_readings_timestamp (timestamp),

    CONSTRAINT fk_readings_meter
        FOREIGN KEY (meter_id) REFERENCES meters(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_readings_customer
        FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------- Predictions ----------
CREATE TABLE predictions (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id         INT UNSIGNED    NOT NULL,
    bilstm_score        DECIMAL(8,6)    NOT NULL COMMENT 'Bi-LSTM branch theft probability',
    transformer_score   DECIMAL(8,6)    NOT NULL COMMENT 'Transformer branch theft probability',
    fused_score         DECIMAL(8,6)    NOT NULL COMMENT 'Fusion model theft probability',
    risk_score          SMALLINT UNSIGNED NOT NULL COMMENT 'Mapped risk score 0-100',
    risk_level          ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    model_version       VARCHAR(20)     NOT NULL DEFAULT 'v1.0.0',
    sequence_start      DATETIME        NULL COMMENT 'Start of input consumption window',
    sequence_end        DATETIME        NULL COMMENT 'End of input consumption window',
    predicted_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_predictions_customer (customer_id),
    INDEX idx_predictions_at (predicted_at),
    INDEX idx_predictions_risk (risk_level),
    INDEX idx_predictions_customer_at (customer_id, predicted_at),

    CONSTRAINT fk_predictions_customer
        FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------- Alerts ----------
CREATE TABLE alerts (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id     INT UNSIGNED    NOT NULL,
    prediction_id   INT UNSIGNED    NULL,
    severity        ENUM('info', 'warning', 'high', 'critical') NOT NULL DEFAULT 'warning',
    status          ENUM('open', 'investigating', 'resolved', 'false_positive') NOT NULL DEFAULT 'open',
    title           VARCHAR(255)    NOT NULL,
    message         TEXT            NOT NULL,
    resolved_by     INT UNSIGNED    NULL,
    resolved_at     DATETIME        NULL,
    notes           TEXT            NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_alerts_status (status),
    INDEX idx_alerts_severity (severity),
    INDEX idx_alerts_customer (customer_id),
    INDEX idx_alerts_created (created_at),

    CONSTRAINT fk_alerts_customer
        FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_alerts_prediction
        FOREIGN KEY (prediction_id) REFERENCES predictions(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_alerts_resolved_by
        FOREIGN KEY (resolved_by) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------- Weather Data ----------
CREATE TABLE weather_data (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    region          VARCHAR(100)    NOT NULL,
    timestamp       DATETIME        NOT NULL,
    temperature_c   DECIMAL(5,2)    NULL,
    humidity_pct    DECIMAL(5,2)    NULL,
    wind_speed_ms   DECIMAL(6,2)    NULL,
    pressure_hpa    DECIMAL(7,2)    NULL,
    weather_condition VARCHAR(50)   NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE INDEX uq_weather_region_ts (region, timestamp),
    INDEX idx_weather_timestamp (timestamp)
) ENGINE=InnoDB;

-- ---------- Reports ----------
CREATE TABLE reports (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    generated_by    INT UNSIGNED    NOT NULL,
    report_type     ENUM('theft_summary', 'risk_assessment', 'alert_digest', 'customer_report', 'custom') NOT NULL,
    title           VARCHAR(255)    NOT NULL,
    format          ENUM('pdf', 'csv') NOT NULL DEFAULT 'pdf',
    file_path       VARCHAR(500)    NULL,
    file_size_bytes INT UNSIGNED    NULL,
    parameters      JSON            NULL COMMENT 'Report generation parameters',
    status          ENUM('pending', 'generating', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    error_message   TEXT            NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME        NULL,

    INDEX idx_reports_generated_by (generated_by),
    INDEX idx_reports_created (created_at),
    INDEX idx_reports_status (status),

    CONSTRAINT fk_reports_user
        FOREIGN KEY (generated_by) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------- Activity Logs (Audit Trail) ----------
CREATE TABLE activity_logs (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED    NULL,
    action          VARCHAR(50)     NOT NULL COMMENT 'e.g. login, create, update, delete, predict',
    entity_type     VARCHAR(50)     NOT NULL COMMENT 'e.g. user, customer, alert, prediction',
    entity_id       INT UNSIGNED    NULL,
    details         JSON            NULL,
    ip_address      VARCHAR(45)     NULL,
    user_agent      VARCHAR(500)    NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_activity_user (user_id),
    INDEX idx_activity_created (created_at),
    INDEX idx_activity_entity (entity_type, entity_id),
    INDEX idx_activity_action (action),

    CONSTRAINT fk_activity_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;
