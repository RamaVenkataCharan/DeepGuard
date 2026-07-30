# DeepGuard: AI-Powered Electricity Theft & Predictive Risk Analytics Platform

> **Project Report & Technical Documentation**  
> **System Name**: DeepGuard  
> **Domain**: Smart Grid Security & Predictive Risk Analytics  
> **Core Architecture**: Hybrid Bi-LSTM + Transformer Neural Network | Flask REST API | Celery Task Queue | React Dashboard  

---

## 1. Executive Summary

**DeepGuard** is an end-to-end, enterprise-ready artificial intelligence platform engineered to detect non-technical losses (electricity theft) and predict crop/agricultural utility risks using high-frequency smart meter time-series data.

By combining modern deep learning (Bi-Directional Long Short-Term Memory networks and Transformer multi-head attention mechanisms) with an asynchronous distributed backend architecture (Flask, Celery, Redis, and PostgreSQL/SQLite), DeepGuard provides utility companies and field auditors with real-time anomaly detection, risk profiling, automated alert management, and on-demand analytical reporting.

---

## 2. System Architecture Overview

```
                                    +-----------------------+
                                    |   External Data       |
                                    | (Smart Meters / IoT)  |
                                    +-----------+-----------+
                                                |
                                                v
+------------------+   HTTP Requests    +-------+-------+   Task Queue    +------------------+
|                  | -----------------> |               | --------------> |                  |
|  React Frontend  |                    | Flask API     |                 |  Celery Worker   |
| (Vite + Tailwind)| <----------------- | (REST Endpoints) <------------- | (Background Jobs)|
+------------------+    JSON Response   +-------+-------+   Result/Status +--------+---------+
                                                |                                  |
                                                |                                  v
                                                |                         +--------+---------+
                                                |                         |   ML Pipeline    |
                                                |                         | (Inference Engine|
                                                |                         +--------+---------+
                                                v                                  |
                                        +-------+-------+                          |
                                        |  SQL Database | <------------------------+
                                        | (Users, Risk, |   Store Predictions & Alerts
                                        | Reports, etc) |
                                        +---------------+
```

---

## 3. Machine Learning & Time-Series Pipeline

### 3.1 Data Preparation & Preprocessing (`ml/preprocessing/preprocess.py`)

The ML subsystem processes time-series records from the State Grid Corporation of China (SGCC) Smart Meter Dataset using a robust 7-step pipeline:

| Step | Component | Description & Specification |
| :--- | :--- | :--- |
| **1** | **Loading & Reshaping** | Converts wide-format daily kWh columns into clean long-format `(CONS_NO, date, consumption, FLAG)`. |
| **2** | **Cleaning & Interpolation** | Flag negative/sub-zero consumption records as NaN. Performs per-customer linear interpolation with fallback forward/backward fills at boundaries. Caps outliers beyond $3.5\sigma$. |
| **3** | **Per-Customer Scaling** | Applies individual Min-Max scaling per customer baseline: $(x - \text{min}) / (\text{max} - \text{min} + \epsilon)$. Preserves scaler objects for exact inverse scaling. |
| **4** | **3D Sliding Windows** | Converts long series into 3D tensors of shape `(num_samples, 14, 1)` with a 14-day window size and 7-day stride. |
| **5** | **Feature Engineering** | Extracts 8 auxiliary statistical and temporal features per window: `[mean, std, min, max, skewness, kurtosis, day-over-day delta, weekday_vs_weekend_ratio]`. |
| **6** | **Class Imbalance** | Calculates loss function class weights `{0: 0.556, 1: 5.0}` and applies optional SMOTE oversampling on the 2D extracted feature space `X_feat` (150 $\rightarrow$ 270 samples). *Note: SMOTE is avoided on raw 3D sequences to preserve temporal autocorrelation.* |
| **7** | **Stratified Customer Split** | Splits datasets by **Customer ID** (70% Train, 15% Val, 15% Test) to guarantee 0% data leakage across window boundaries. |

---

## 4. Backend & API Infrastructure

### 4.1 Core Technologies
- **Framework**: Flask (Python 3.10) with Application Factory pattern.
- **Database ORM**: Flask-SQLAlchemy with SQLite (`deepguard.db`) and PostgreSQL support.
- **Task Queue**: Celery with Redis broker for non-blocking prediction runs and PDF/CSV report generation.
- **Security**: JWT (`flask-jwt-extended`) with BCrypt password hashing.

### 4.2 Database Models
- `User`: User authentication, hashed credentials, roles (`Admin`, `Analyst`).
- `Customer`: Client profile metadata, meter ID (`CONS_NO`), tariff category, feeder line, sanctioned load.
- `Prediction`: Model inference logs, risk scores, risk levels, feature snapshots.
- `Alert`: Triggered warnings, risk severity (Low/Medium/High/Critical), status.
- `Report`: Asynchronous export job tracking (PDF/CSV formats, parameters, file paths).

---

## 5. Frontend & UI System

- **Technology Stack**: React, Vite, Tailwind CSS.
- **Key Modules**:
  - **Overview Dashboard**: High-level KPI widgets (Active Alerts, High-Risk Accounts, Monitored Acreage).
  - **Risk Analytics Center**: Interactive temporal risk charts and anomaly heatmaps.
  - **Customer & Meter Manager**: Table views with search, filter, and regional grouping.
  - **Alert Digest & Resolution Manager**: Actionable list for acknowledging, investigating, or closing high-priority risk alerts.
  - **Report Builder & Exporter**: Form interface for requesting asynchronous PDF/CSV risk reports.

---

## 6. Execution & Verification Benchmarks

The complete system pipeline was tested and verified end-to-end:

- **Raw Customers Processed**: 50 (30 daily consumption columns)
- **Raw Missing Values**: 6.67% $\rightarrow$ **0.0%** post-cleaning
- **Total Sliding Windows**: **150 tensors** (Shape: `150 x 14 x 1`)
- **Class Weights Computed**: `Normal (0): 0.556`, `Theft (1): 5.000`
- **SMOTE Oversampled Features**: **150 $\rightarrow$ 270 samples**
- **Customer Leakage Split Ratio**: **102 Train / 24 Val / 24 Test** (0 overlap)

---

## 7. Future Strategic Roadmap

### ⚡ Phase 1: Near-Term Enhancements
1. **Real-Time Telemetry Ingestion**: WebSocket & MQTT protocols for continuous smart meter / IoT soil sensor data stream.
2. **Graphical PDF Reports**: Embedded Matplotlib / Plotly charts inside exported PDF summary reports via ReportLab/WeasyPrint.
3. **Enterprise RBAC**: Fine-grained access policies for `Admin`, `Auditor`, `Agronomist`, and `Field Inspector`.

### 🚀 Phase 2: Advanced ML & Spatial Analytics
1. **Geospatial Anomaly Mapping**: Leaflet / Mapbox integration with Landsat & Sentinel satellite imagery overlays.
2. **Model Monitoring & Drift Detection**: Integration with MLflow / Evidently AI to detect distribution drift and trigger automatic retrain loops.
3. **SMS & Push Alerts**: Automated Twilio / SendGrid alerts when critical risk thresholds are crossed.

---
*Report Generated: July 30, 2026*  
*DeepGuard Development & Engineering Team*
