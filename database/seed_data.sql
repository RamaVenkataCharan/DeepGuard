-- ============================================================
-- DeepGuard Seed Data
-- Demo users, sample customers, meters, readings, predictions, alerts
-- ============================================================

USE deepguard;

-- ---------- Users ----------
-- Passwords: admin123, analyst123, viewer123  (bcrypt hashed)
INSERT INTO users (email, password_hash, full_name, role, is_active) VALUES
('admin@deepguard.io',   '$2b$12$LJ3m4ys3Lz0QDOBKhJ8hZOX8Mz8UEQ1JXhF9T7nK3XjJjKvE7MWq', 'System Admin',   'admin',   TRUE),
('analyst@deepguard.io', '$2b$12$LJ3m4ys3Lz0QDOBKhJ8hZOX8Mz8UEQ1JXhF9T7nK3XjJjKvE7MWq', 'Jane Analyst',   'analyst', TRUE),
('viewer@deepguard.io',  '$2b$12$LJ3m4ys3Lz0QDOBKhJ8hZOX8Mz8UEQ1JXhF9T7nK3XjJjKvE7MWq', 'John Viewer',    'viewer',  TRUE);

-- ---------- Customers ----------
INSERT INTO customers (customer_code, name, address, region, city, account_status, connection_type) VALUES
('CUST-001', 'Rajesh Kumar',       '45 MG Road, Sector 12',         'North Delhi',   'New Delhi',  'active', 'residential'),
('CUST-002', 'Priya Sharma',       '123 Gandhi Nagar, Block B',     'South Delhi',   'New Delhi',  'active', 'residential'),
('CUST-003', 'TechPark Solutions', '500 IT Park, Phase II',         'Gurgaon',       'Gurgaon',    'active', 'commercial'),
('CUST-004', 'Amit Patel',         '78 Nehru Colony',               'East Delhi',    'New Delhi',  'active', 'residential'),
('CUST-005', 'GreenLeaf Textiles', '200 Industrial Area, Plot 15',  'Noida',         'Noida',      'active', 'industrial'),
('CUST-006', 'Sunita Verma',       '33 Laxmi Nagar, Flat 4C',       'East Delhi',    'New Delhi',  'active', 'residential'),
('CUST-007', 'Metro Mall Complex', '1 Central Avenue',              'South Delhi',   'New Delhi',  'active', 'commercial'),
('CUST-008', 'Vikram Singh',       '90 Saket, J Block',             'South Delhi',   'New Delhi',  'suspended', 'residential'),
('CUST-009', 'Ananya Reddy',       '15 Jubilee Hills',              'Hyderabad',     'Hyderabad',  'active', 'residential'),
('CUST-010', 'SteelWorks Ltd.',    '400 MIDC Industrial Estate',    'Pune',          'Pune',       'active', 'industrial');

-- ---------- Meters ----------
INSERT INTO meters (customer_id, meter_number, meter_type, install_date, is_active) VALUES
(1,  'SM-2024-00001', 'smart',   '2023-01-15', TRUE),
(2,  'SM-2024-00002', 'smart',   '2023-02-20', TRUE),
(3,  'SM-2024-00003', 'smart',   '2023-03-10', TRUE),
(4,  'SM-2024-00004', 'smart',   '2023-04-05', TRUE),
(5,  'SM-2024-00005', 'smart',   '2023-05-12', TRUE),
(6,  'SM-2024-00006', 'smart',   '2023-06-01', TRUE),
(7,  'SM-2024-00007', 'smart',   '2023-07-18', TRUE),
(8,  'SM-2024-00008', 'digital', '2022-11-25', TRUE),
(9,  'SM-2024-00009', 'smart',   '2023-08-08', TRUE),
(10, 'SM-2024-00010', 'smart',   '2023-09-30', TRUE);

-- ---------- Meter Readings (sample 30 days for customers 1-3) ----------
-- Customer 1: Normal consumption pattern (~15-25 kWh/day)
INSERT INTO meter_readings (meter_id, customer_id, timestamp, consumption_kwh, quality_flag) VALUES
(1, 1, '2024-06-01 00:00:00', 18.5200, 'valid'),
(1, 1, '2024-06-02 00:00:00', 19.1000, 'valid'),
(1, 1, '2024-06-03 00:00:00', 17.8400, 'valid'),
(1, 1, '2024-06-04 00:00:00', 20.3100, 'valid'),
(1, 1, '2024-06-05 00:00:00', 16.9500, 'valid'),
(1, 1, '2024-06-06 00:00:00', 21.2000, 'valid'),
(1, 1, '2024-06-07 00:00:00', 22.8800, 'valid'),
(1, 1, '2024-06-08 00:00:00', 19.4300, 'valid'),
(1, 1, '2024-06-09 00:00:00', 18.1100, 'valid'),
(1, 1, '2024-06-10 00:00:00', 20.7600, 'valid'),
(1, 1, '2024-06-11 00:00:00', 17.2200, 'valid'),
(1, 1, '2024-06-12 00:00:00', 19.9400, 'valid'),
(1, 1, '2024-06-13 00:00:00', 21.5500, 'valid'),
(1, 1, '2024-06-14 00:00:00', 18.8800, 'valid');

-- Customer 2: Suspicious pattern — sudden drops (possible theft)
INSERT INTO meter_readings (meter_id, customer_id, timestamp, consumption_kwh, quality_flag) VALUES
(2, 2, '2024-06-01 00:00:00', 22.1000, 'valid'),
(2, 2, '2024-06-02 00:00:00', 21.5500, 'valid'),
(2, 2, '2024-06-03 00:00:00', 23.4000, 'valid'),
(2, 2, '2024-06-04 00:00:00',  5.2000, 'valid'),
(2, 2, '2024-06-05 00:00:00',  3.8000, 'valid'),
(2, 2, '2024-06-06 00:00:00',  4.1000, 'valid'),
(2, 2, '2024-06-07 00:00:00', 22.9000, 'valid'),
(2, 2, '2024-06-08 00:00:00', 21.3000, 'valid'),
(2, 2, '2024-06-09 00:00:00',  2.5000, 'valid'),
(2, 2, '2024-06-10 00:00:00',  3.1000, 'valid'),
(2, 2, '2024-06-11 00:00:00', 23.8000, 'valid'),
(2, 2, '2024-06-12 00:00:00', 20.9000, 'valid'),
(2, 2, '2024-06-13 00:00:00',  4.6000, 'valid'),
(2, 2, '2024-06-14 00:00:00',  2.9000, 'valid');

-- Customer 3: High commercial usage (~80-120 kWh/day), normal
INSERT INTO meter_readings (meter_id, customer_id, timestamp, consumption_kwh, quality_flag) VALUES
(3, 3, '2024-06-01 00:00:00',  95.2000, 'valid'),
(3, 3, '2024-06-02 00:00:00',  12.5000, 'valid'),
(3, 3, '2024-06-03 00:00:00', 102.8000, 'valid'),
(3, 3, '2024-06-04 00:00:00',  98.1000, 'valid'),
(3, 3, '2024-06-05 00:00:00', 110.4000, 'valid'),
(3, 3, '2024-06-06 00:00:00', 105.9000, 'valid'),
(3, 3, '2024-06-07 00:00:00',  15.3000, 'valid'),
(3, 3, '2024-06-08 00:00:00',  88.7000, 'valid'),
(3, 3, '2024-06-09 00:00:00',  11.2000, 'valid'),
(3, 3, '2024-06-10 00:00:00', 101.5000, 'valid'),
(3, 3, '2024-06-11 00:00:00', 107.3000, 'valid'),
(3, 3, '2024-06-12 00:00:00',  99.8000, 'valid'),
(3, 3, '2024-06-13 00:00:00', 112.1000, 'valid'),
(3, 3, '2024-06-14 00:00:00',  13.9000, 'valid');

-- ---------- Predictions ----------
INSERT INTO predictions (customer_id, bilstm_score, transformer_score, fused_score, risk_score, risk_level, model_version, predicted_at) VALUES
(1, 0.082000, 0.065000, 0.073000, 12,  'low',      'v1.0.0', '2024-06-15 10:00:00'),
(2, 0.891000, 0.923000, 0.912000, 91,  'critical',  'v1.0.0', '2024-06-15 10:00:00'),
(3, 0.120000, 0.095000, 0.105000, 18,  'low',      'v1.0.0', '2024-06-15 10:00:00'),
(4, 0.445000, 0.510000, 0.480000, 52,  'high',     'v1.0.0', '2024-06-15 10:00:00'),
(5, 0.210000, 0.180000, 0.195000, 28,  'medium',   'v1.0.0', '2024-06-15 10:00:00'),
(6, 0.670000, 0.720000, 0.698000, 72,  'high',     'v1.0.0', '2024-06-15 10:00:00'),
(7, 0.055000, 0.042000, 0.048000,  8,  'low',      'v1.0.0', '2024-06-15 10:00:00'),
(8, 0.780000, 0.815000, 0.800000, 82,  'critical', 'v1.0.0', '2024-06-15 10:00:00'),
(9, 0.310000, 0.280000, 0.295000, 38,  'medium',   'v1.0.0', '2024-06-15 10:00:00'),
(10, 0.150000, 0.130000, 0.140000, 22, 'low',      'v1.0.0', '2024-06-15 10:00:00');

-- ---------- Alerts ----------
INSERT INTO alerts (customer_id, prediction_id, severity, status, title, message, created_at) VALUES
(2, 2, 'critical', 'open',          'Critical Theft Risk Detected',        'Customer CUST-002 shows a fused theft probability of 91.2%. Consumption dropped by 80% on multiple days — strongly indicative of meter tampering.', '2024-06-15 10:05:00'),
(8, 8, 'critical', 'investigating', 'Critical Theft Risk Detected',        'Customer CUST-008 (suspended account) shows a fused theft probability of 80.0%. Possible unauthorized reconnection.', '2024-06-15 10:05:00'),
(6, 6, 'high',     'open',          'High Theft Risk Detected',            'Customer CUST-006 shows a fused theft probability of 69.8%. Irregular consumption spikes and drops detected.', '2024-06-15 10:05:00'),
(4, 4, 'high',     'open',          'High Theft Risk Detected',            'Customer CUST-004 shows a fused theft probability of 48.0%. Moderate anomaly in consumption pattern.', '2024-06-15 10:05:00'),
(5, 5, 'warning',  'resolved',      'Medium Risk — Consumption Anomaly',   'Customer CUST-005 industrial consumption variance exceeded threshold. Verified as seasonal production shift.', '2024-06-15 10:05:00'),
(9, 9, 'warning',  'false_positive', 'Medium Risk — Consumption Anomaly',  'Customer CUST-009 flagged due to low consumption during vacation period. Confirmed false positive.', '2024-06-15 10:05:00');

-- ---------- Weather Data (sample for Delhi region) ----------
INSERT INTO weather_data (region, timestamp, temperature_c, humidity_pct, wind_speed_ms, pressure_hpa, weather_condition) VALUES
('North Delhi', '2024-06-01 00:00:00', 42.5, 28.0, 3.2, 1005.0, 'Clear'),
('North Delhi', '2024-06-02 00:00:00', 43.1, 25.0, 2.8, 1004.0, 'Clear'),
('North Delhi', '2024-06-03 00:00:00', 41.8, 32.0, 4.1, 1006.0, 'Haze'),
('North Delhi', '2024-06-04 00:00:00', 38.2, 55.0, 5.5, 1003.0, 'Cloudy'),
('North Delhi', '2024-06-05 00:00:00', 35.0, 72.0, 6.8, 1001.0, 'Rain'),
('North Delhi', '2024-06-06 00:00:00', 36.5, 65.0, 4.2, 1003.0, 'Cloudy'),
('North Delhi', '2024-06-07 00:00:00', 40.2, 35.0, 3.0, 1005.0, 'Clear'),
('North Delhi', '2024-06-08 00:00:00', 41.0, 30.0, 2.5, 1006.0, 'Clear'),
('North Delhi', '2024-06-09 00:00:00', 39.5, 45.0, 3.8, 1004.0, 'Haze'),
('North Delhi', '2024-06-10 00:00:00', 37.0, 60.0, 5.0, 1002.0, 'Cloudy'),
('North Delhi', '2024-06-11 00:00:00', 34.5, 78.0, 7.2, 1000.0, 'Rain'),
('North Delhi', '2024-06-12 00:00:00', 33.0, 82.0, 8.1, 999.0,  'Rain'),
('North Delhi', '2024-06-13 00:00:00', 36.8, 58.0, 4.5, 1003.0, 'Cloudy'),
('North Delhi', '2024-06-14 00:00:00', 39.2, 38.0, 3.1, 1005.0, 'Clear');
