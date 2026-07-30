# DeepGuard — System Overview, Architecture & Project Roadmap

## 1. Introduction & Executive Summary
**DeepGuard** is an AI-powered predictive analytics, risk management, and decision-support platform designed for agricultural monitoring and crop/yield failure prediction. It combines machine learning pipelines, asynchronous task handling, real-time alerting, and an interactive web dashboard to provide actionable insights for field management and crop risk mitigation.

---

## 2. What Is Developed (Current Implementation Status)

### 🔹 **Backend Core (Flask RESTful API)**
- **Framework**: Flask microframework with application factory pattern (`backend/app/__init__.py`).
- **Database & ORM**: Flask-SQLAlchemy with SQLite (development `deepguard.db`) / PostgreSQL compatibility.
  - **Models**:
    - `User`: Authentication, roles, and password hashing (`backend/app/models/user.py`).
    - `Customer`: Client profiles, smart meter ID (`CONS_NO`), tariff category, feeder line, sanctioned load (`backend/app/models/customer.py`).
    - `Prediction`: ML predictions history, risk scores, features, status (`backend/app/models/prediction.py`).
    - `Alert`: Triggered warnings, risk severity (Low/Medium/High/Critical), status (`backend/app/models/alert.py`).
    - `Report`: Generated analysis reports, metrics, export paths (`backend/app/models/report.py`).
- **Security & Auth**: JWT-based authentication (`flask-jwt-extended`) with protected route endpoints (`backend/app/api/auth.py`).
- **Asynchronous Task Queue**: Celery with Redis broker integration (`backend/app/tasks/`) for background execution of batch predictions and heavy report generation.
- **REST Endpoints**:
  - `POST /api/v1/auth/login`, `POST /api/v1/auth/register` — Auth management.
  - `GET/POST /api/v1/customers` — Farm/customer entity management.
  - `GET/POST /api/v1/predictions` — Trigger risk evaluation and query prediction logs.
  - `GET /api/v1/alerts` — Fetch and acknowledge risk alerts.
  - `GET/POST /api/v1/reports` — Generate & download PDF/CSV risk reports.
  - `GET /api/v1/dashboard/summary` — Aggregated KPI metrics for dashboard view.
  - `GET /api/v1/weather` — Real-time weather data integration for risk modeling.

### 🔹 **Machine Learning Pipeline (`/ml`)**
- **Model Architecture**: Multi-factor ML models for risk evaluation (crop disease, drought/heat stress, yield anomaly detection).
- **Preprocessing Engine**: Custom feature transformers handling climate indices, soil metrics, and historical yield trend vectors (`ml/preprocessing/`).
- **Inference Service**: Modular inference runner (`ml/inference/`) wrapped for standalone execution and backend API consumption.
- **Model Storage**: Versioned artifacts (`ml/artifacts/`) containing trained weights and scalar encoders.

### 🔹 **Frontend Application (`/frontend`)**
- **Framework**: React (Vite bundle) with Tailwind CSS styling.
- **UI Components & Pages**:
  - **Dashboard Overview**: Summary widgets (active alerts, high-risk accounts, total utility consumption monitored).
  - **Risk Analytics**: Interactive chart visualizations for risk trend analysis over time.
  - **Customer & Field Management**: Table & card views for managing farms, crop types, and regional parameters.
  - **Alert Center**: Real-time alert list with severity indicators and resolution actions.
  - **Report Builder**: Form to request on-demand risk assessments and export PDF reports.

### 🔹 **Infrastructure & Deployment Configuration**
- **Containerization**: `docker-compose.yml` (development) and `docker-compose.prod.yml` (production setup).
- **Services Containers**: Flask API container, Celery Worker container, Redis broker, PostgreSQL database container, and Nginx reverse proxy.
- **Automation**: `Makefile` with targets for running migrations, tests, local dev servers, and docker builds.

---

## 3. Project Arc & System Flow Architecture

```
                                    +-----------------------+
                                    |   External Data       |
                                    | (Weather API / IoT)   |
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

### **Data & Execution Arc**:
1. **Data Ingestion & Inputs**: Field parameters, crop type, location, and weather indicators are sent from the frontend or API clients.
2. **REST Processing & Auth**: Flask API validates authentication token, formats payload, and checks current cache/database records.
3. **Async ML Execution**: For heavy batch predictions, the request is offloaded to Celery worker queue to keep API response non-blocking.
4. **ML Inference & Risk Score Calculation**: Machine learning pipelines load normalized features, execute inference, evaluate threshold triggers (e.g. Risk Score > 0.75), and generate alert records if necessary.
5. **Persist & Notify**: Results, predictions, and alerts are stored in the SQL database; socket/API notifications are available for frontend status updates.
6. **Visualization & Export**: Frontend renders interactive dashboard charts and allows downloading compiled PDF/CSV summary reports.

---

## 4. Recommendations on What to Add Next (Roadmap)

To elevate DeepGuard into an enterprise-ready, production-grade intelligence platform, the following features and enhancements should be prioritized:

### ⚡ **Short-Term Enhancements (Phase 1: Operational Polish)**
1. **Real-time IoT Telemetry Integration**:
   - Add WebSocket / MQTT ingestion pipeline for real-time field soil sensors (moisture, temperature, NPK values).
2. **Enhanced PDF & Excel Export Builder**:
   - Upgrade `report_service.py` to embed generated matplotlib/chart graphics directly inside exported PDF reports.
3. **Role-Based Access Control (RBAC)**:
   - Implement fine-grained permissions (`Admin`, `Agronomist`, `Field Worker`, `Client View`) on Flask API routes and React component trees.

### 🚀 **Medium-Term Features (Phase 2: Advanced ML & Data Insights)**
1. **Satellite & Geospatial Mapping Integration**:
   - Integrate Sentinel-2 / Landsat NDVI imagery overlays on an interactive Leaflet/Mapbox map in the frontend.
2. **Automated ML Retraining & Drift Monitoring**:
   - Setup Evidently AI or MLflow tracking to monitor data drift and schedule automated model retraining when weather distribution shifts occur.
3. **Automated Notification Channels**:
   - Integrate Twilio (SMS) and SendGrid (Email) alerting when critical risk thresholds are exceeded for a customer field.

### 🏭 **Long-Term Enterprise Roadmap (Phase 3: Scale & Reliability)**
1. **Kubernetes Deployment (Helm Charts)**:
   - Create Helm charts under `infra/k8s/` for autoscaling API pods and Celery workers during seasonal peaks.
2. **Multi-Tenant Architecture**:
   - Implement logical schema isolation per enterprise customer for strict data privacy and compliance.
3. **Offline / Mobile Field App Capability**:
   - Add PWA (Progressive Web App) offline caching capability for field workers operating in low-connectivity rural regions.

---
*Document updated on: July 30, 2026*
