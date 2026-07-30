# DeepGuard: Electricity Theft Detection System Project Summary

This document summarizes the current development phase, completed modules, file structure, model architectures, and remaining steps required for production deployment.

---

## 1. Executive Summary & Accomplishments

We have successfully developed, verified, and integrated the **DeepGuard** electricity theft detection system. All ML branches, backend schemas, alert generators, and frontend dashboards are integrated and verified end-to-end against a verified database seed.

### Completed Tasks
1. **Smart-Meter Customer Schema Refactoring**:
   * Removed legacy agricultural fields (`location`, `acreage`, `crop_type`).
   * Added utility-focused fields: `meter_id`, `tariff_category`, `feeder_line`, `region_code`, `sanctioned_load_kw`, and capitalized `connection_type`.
   * Created Alembic migration (`002_update_customer_schema.py`) including SQL data migration to convert lowercase categories (`residential` $\rightarrow$ `Residential`).
2. **Leakage-Free Preprocessing Pipeline**:
   * Cleans raw inputs, interpolates gaps, and applies per-customer Min-Max normalization.
   * Shapes inputs into 14-day sequence windows with a 7-day stride.
   * Extracts an 8-factor statistical auxiliary vector (mean, std dev, skewness, kurtosis, Day-over-Day delta, weekend ratio, etc.).
   * Splits data by customer ID (Customer-level stratified split) to guarantee **zero data leakage** between splits.
3. **Hybrid Sequence Deep Learning Architecture**:
   * Stacked Bi-LSTM branch capturing sequential trends.
   * Multi-head Self-Attention Transformer branch utilizing positional encodings.
   * Fused late-concatenation model combining temporal features with statistical descriptors (91,329 total parameters).
4. **Leakage-Free Ablation Study**:
   * Evaluated model variants (Hybrid vs Standalone Bi-LSTM vs Standalone Transformer).
   * Audited threshold selection: scans decision boundaries ($\tau$) **strictly on the Validation set**, applying the optimum once to the **Test set** to eliminate validation leakage.
5. **Non-Linear Risk Scoring Engine**:
   * Converts sigmoid probabilities (0.0-1.0) to a 0-100 Risk Index.
   * Maps validation-selected threshold ($\tau^* = 0.48$) to Risk Index = 50.
   * Uses damping below threshold and acceleration above threshold to prioritize high-risk targets.
6. **Deduplicating Alert Ingestion Service**:
   * Auto-generates alerts in the database if Risk Score $\ge 51$ (High/Critical).
   * Prevents alert fatigue by checking for existing active alerts for the same customer within a 7-day window.
   * Enforces strict state transitions (`open` $\rightarrow$ `investigating` $\rightarrow$ `resolved`/`false_positive`).
7. **Interactive Operations Frontend Dashboard**:
   * Renders KPI metrics, bar charts, and active alert queues.
   * Highlights consumption anomalies on the customer detail graph using Recharts `<ReferenceArea>`.
   * Includes dynamic warning banners that trigger automatically when the dataset source is tagged `synthetic_demo`.

---

## 2. File Structure Directory Tree

```text
DeepGuard/
│
├── database/                   # Database schemas and migrations
│   ├── migrations/             # Alembic migration scripts
│   │   └── versions/           # 002_update_customer_schema.py (ORM updates)
│   └── schema.sql              # Initial database schema setup
│
├── backend/                    # Flask REST API Backend
│   ├── app/
│   │   ├── api/                # REST endpoints (auth, alerts, customers, dashboard)
│   │   ├── models/             # SQLAlchemy ORM models (customer, alert, user, prediction)
│   │   └── services/           # Business logic (alert_service.py lifecycle & dedup)
│   └── seed.py                 # Resets and seeds smart-meter database profiles
│
├── frontend/                   # React.js SPA Frontend
│   └── src/
│       ├── components/         # Reusable UI controls and navbar
│       ├── context/            # AuthContext.jsx session handling
│       ├── services/           # Axios API connection
│       └── pages/              # View pages:
│           ├── Dashboard.jsx   # Overview KPIs & customer directory
│           ├── Alerts.jsx      # Audit Active Queue & status modifications
│           └── CustomerDetail.jsx # 14-Day graph with ReferenceArea anomaly shading
│
└── ml/                         # Machine Learning Pipeline
    ├── config.py               # Model hyperparameters & scaling parameters
    ├── data/
    │   ├── raw/                # Target location for real SGCC CSV dataset
    │   └── validate_raw_data.py# Formats and parses raw data files
    ├── preprocessing/          # Preprocessing logic
    │   ├── preprocess.py       # Main cleaning, normalization, window, and split pipeline
    │   └── verify_split.py     # Independent customer-split leakage auditor
    ├── models/                 # Model builders and execution pipelines
    │   ├── bilstm_model.py     # Stacked Bi-LSTM branch builder
    │   ├── transformer_model.py# Sinusoidal positional encoder & multi-head attention block
    │   ├── fusion_model.py     # Late-fusion concatenation branch assembly
    │   ├── train.py            # Compiles and fits model with AUC-PR early stopping
    │   ├── evaluate.py         # Test split evaluation
    │   └── ablation_study.py   # Run 3-way comparative evaluation
    └── inference/
        └── risk_score.py       # Converts model probability to non-linear 0-100 score
```

---

## 3. Model Architectures & Configurations

The Hybrid Fusion model integrates three parallel branches into a dense neural network:

```mermaid
graph TD
    SeqInput[14-Day Sequence Input (14, 1)] --> BiLSTM[Stacked Bi-LSTM Branch]
    SeqInput --> Trans[Transformer Branch + Sinusoidal PE]
    FeatInput[8D Statistical Features (8,)] --> DenseFeat[Dense Projection]
    
    BiLSTM -->|32d Embedding| Fusion[Late Fusion Concatenation]
    Trans -->|32d Embedding| Fusion
    DenseFeat -->|16d Embedding| Fusion
    
    Fusion -->|80d Joint Embedding| DenseOut[Dense layers & Sigmoid Head]
    DenseOut --> Prob[Theft Probability]
```

### Parameters Summary
* **Stacked Bi-LSTM Branch**: 2 LSTM layers ($64 \rightarrow 32$ units) with $0.2$ recurrent dropout (Trainable parameters: ~78,401).
* **Transformer Branch**: Multi-head attention layer (2 heads, key dimension 16) with sinusoidal positional encoding (Trainable parameters: ~10,209).
* **Auxiliary Feature branch**: Dense projection (16 units) of statistical load descriptors.
* **Late Fusion Concatenation Layer**: Combines embeddings into an 80-dimensional joint representation vector, feeding a sigmoidal classification head (Total Trainable Parameters: **91,329**).

---

## 4. Next Steps: Sourcing and Productionizing

The downstream pipeline is verified and locked. To complete production implementation, the following actions must be taken:

### 📋 Sourcing & Running on Real Data
1. **Sourcing the Real SGCC Dataset**:
   Download the State Grid Corporation of China (SGCC) Smart Meter dataset containing 42,372 customers over 1,035 days and place it at:  
   `ml/data/raw/data.csv`
2. **Execute Data Validation**:
   Run the verification script to validate column counts, date formats, and target imbalances:
   ```bash
   python -m ml.data.validate_raw_data
   ```
3. **Execute Real Preprocessing**:
   Process the dataset into sliding window arrays (recalculates train/val/test splits):
   ```bash
   python -m ml.preprocessing.preprocess
   ```
4. **Real Training & Validation Scan**:
   Trigger model training on the 6.2M windows and run the validation threshold optimizer to establish the production boundary ($\tau^*$):
   ```bash
   python -m ml.models.train
   ```
