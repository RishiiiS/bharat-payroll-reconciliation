# Bharat Payroll Reconciliation Tool

## Overview

This project is a full-stack payroll reconciliation system built for ops and finance teams. It automatically reconstructs expected wages for field workers, reconciles them against actual bank transfers, and provides a beautiful, real-time dashboard to triage discrepancies (underpayments, overpayments, and missing payments).

The system acts as an analytical forensic tool to identify pipeline failures and ensure workers are paid accurately.

---

## 🚀 Key Features

* **Data Normalization:** Cleans and normalizes raw timestamps, phone numbers, and effective-dated wage rates.
* **Worker Identity Matching:** Resolves worker identities using exact phone matches and fuzzy name fallback.
* **Expected Pay Engine:** Computes exact wages factoring in state, role, seniority, and shift duration.
* **Automated Audit Pipeline:** Reconciles expected vs. actual payments, flagging missing transfers, incorrect amounts, and anomalies (e.g. 450-hour shifts, overlapping rates).
* **Validation Suite:** A robust `validate_pipeline.py` script that mathematically proves the integrity of the data and guarantees backend-to-frontend consistency.
* **Real-time Ops Dashboard:** A React/Vite dashboard powered by FastAPI to instantly visualize system health, filter issues, and export CSVs.

---

## 🏗️ Project Structure

```
bharat-payroll-reconciliation/
│
├── backend/
│   ├── financial_audit.py       # Final discrepancy & forensic aggregation
│   ├── main.py                  # API routes
│   ├── reconcile.py             # Shift-to-payment mapping
│   └── server.py                # FastAPI backend serving the React UI
│
├── frontend/                    # Vite + React + Tailwind UI
│   ├── src/
│   │   ├── components/          # Dashboard UI components
│   │   └── App.jsx              # Main React application
│   └── package.json
│
├── data/                        # Raw CSV inputs and pipeline CSV outputs
├── docs/                        # Project documentation (Forensics, Decisions etc.)
│
├── analyze_data.py              # Exploratory data scripts
├── clean_data.py                # Data cleaning logic
├── debug_pay.py                 # Debugging utilities
├── match_workers.py             # Identity resolution logic
├── production_pipeline.py       # Orchestrator for the data pipeline
├── validate_pipeline.py         # Mathematical proofs and validation script
│
├── requirements.txt             # Python dependencies
├── README.md
└── .gitignore# Bharat Payroll Reconciliation Tool

## Key Finding

362 out of 2,617 shifts (~13.8%) are missing corresponding bank transfers, resulting in a total discrepancy of ₹836,831.88.

The system calculates wages correctly, but fails to consistently convert valid shifts into payments. Restoring these missing payments reduces the discrepancy by approximately 99.1%, indicating a systemic issue in the payout pipeline.

---

## What This Project Does

* Reconstructs expected wages at shift-level granularity
* Matches shifts to bank transfers
* Identifies missing payments, underpayments, overpayments, and anomalies
* Provides a dashboard for operational triage
* Validates outputs using mathematical consistency checks

---

## Overview

This project is a full-stack payroll reconciliation system designed for operations and finance teams. It ingests raw data, reconstructs what each worker should have been paid, and compares it against actual bank transfers.

The system functions as a forensic tool to identify discrepancies, quantify financial impact, and diagnose failures in the payment pipeline.

---

## How It Works

1. Data is cleaned and normalized to standardize timestamps, phone numbers, and inconsistent entries
2. Worker identities are resolved using phone numbers with fallback name matching
3. Expected pay is computed using role, state, seniority, and effective-dated wage rates
4. Bank transfers are matched against shifts
5. Expected and actual payments are reconciled
6. Validation checks ensure mathematical consistency
7. Results are visualized in a dashboard for analysis

---

## Key Features

* Data normalization for inconsistent real-world inputs
* Worker identity resolution across multiple formats
* Accurate expected pay computation using business rules
* Automated reconciliation pipeline with anomaly detection
* Validation script to verify correctness and consistency
* Interactive dashboard for exploring discrepancies
* Shift-level drilldown for detailed inspection
* Exportable outputs for downstream use

---

## Why This Matters

This is not just a technical problem but a financial and operational one.

Workers are systematically underpaid due to missing payments. This introduces trust, compliance, and reporting risks. Manual reconciliation at this scale is not feasible.

This system enables faster detection of discrepancies, accurate financial reporting, and more reliable payroll operations.

---

## Project Structure

```
bharat-payroll-reconciliation/
│
├── backend/
│   ├── financial_audit.py
│   ├── reconcile.py
│   ├── server.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── App.jsx
│
├── data/
├── docs/
│
├── clean_data.py
├── match_workers.py
├── production_pipeline.py
├── validate_pipeline.py
│
├── requirements.txt
├── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd bharat-payroll-reconciliation
```

---

### 2. Setup the backend

```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
# venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

---

### 3. Setup the frontend

```bash
cd frontend
npm install
cd ..
```

---

## Running the System

### Step 1: Run the data pipeline

```bash
python backend/financial_audit.py
```

This generates:

* data/shift_level_expected_pay.csv
* data/financial_audit_results.csv

---

### Step 2: Validate the pipeline (optional)

```bash
python validate_pipeline.py
```

This verifies:

* row-level correctness
* aggregation consistency
* alignment with frontend data

---

### Step 3: Start the backend

```bash
python backend/server.py
```

The API runs at:
http://127.0.0.1:8000

---

### Step 4: Start the frontend

```bash
cd frontend
npm run dev
```

The dashboard runs at:
http://localhost:5173

---

## Using the Dashboard

* View overall discrepancy and worker classifications
* Filter workers by status
* Expand rows to inspect shift-level details
* Identify missing payments, incorrect amounts, and anomalies
* Export results for operational or financial workflows

---

## Forensics

362 out of 2,617 shifts (~13.8%) are missing corresponding bank transfers, which drives the majority of the discrepancy.

Total discrepancy: ₹836,831.88
Fixing missing payments resolves approximately 99.1% of the gap

See docs/FORENSICS.md for a detailed breakdown of findings, validation, and root cause analysis.

---

## Design Principles

* Read-only backend serving processed data
* No hardcoded values in the frontend
* All metrics derived dynamically from datasets
* ₹100 tolerance used to avoid rounding noise
* Consistency between validation output and UI

---

## Production Note

In this implementation, global metrics are derived directly from datasets in the frontend to ensure consistency with validation results.

In a production system, these values would be exposed through backend APIs for real-time accuracy.

---

## Status

The pipeline has been validated at row level, aggregation level, and system level. The reconciliation results are consistent, and the frontend accurately reflects backend outputs.

```

---

## 🛠️ Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd bharat-payroll-reconciliation
```

### 2. Setup the Python Backend

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate      # Mac/Linux
# venv\Scripts\activate       # Windows

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Setup the React Frontend

```bash
cd frontend
npm install
cd ..
```

---

## ⚙️ Running the System

To use the tool, you must first run the data pipeline to generate the audit results, and then start the frontend and backend servers.

### Step 1: Run the Data Pipeline

This step executes the pipeline orchestrator, ingests raw data, computes financial audits, and generates the processed CSVs.

```bash
# Ensure you are in the root directory and your venv is active
python backend/financial_audit.py
```
*Outputs generated: `data/shift_level_expected_pay.csv` and `data/financial_audit_results.csv`*

### Step 2: Validate the Pipeline (Optional but Recommended)

Mathematically prove that the pipeline generated accurate results and exactly matches frontend expectations:
```bash
python validate_pipeline.py
```

### Step 3: Start the Backend API

Start the FastAPI server which serves the data to the UI:

```bash
# Ensure you are in the root directory
python backend/server.py
```
*The API will run on `http://127.0.0.1:8000`*

### Step 4: Start the Frontend Dashboard

Open a **new terminal window**, navigate to the frontend folder, and start the Vite dev server:

```bash
cd frontend
npm run dev
```
*The Dashboard will run on `http://localhost:5173`*

---

## 📊 Key Insight & Forensics

The system successfully identified the root cause of a massive ₹836,831.88 payroll discrepancy:

> **~13.8% of valid shifts (362 shifts) are missing corresponding bank transfers.**

Restoring these missing payments resolves **~99.1%** of the entire discrepancy.

For a comprehensive breakdown of the anomalies, overlapping rates, and mathematical proofs, please read [FORENSICS.md](./docs/FORENSICS.md).

---

## 📝 Design Principles

* **Read-Only Backend:** The FastAPI backend serves static CSVs generated by the pipeline. No database is required, making it highly portable.
* **Zero UI Hardcoding:** The React dashboard dynamically reads authoritative totals and calculates percentages using `useMemo` hooks natively from the raw CSV assets.
* **Tolerance Handling:** A strict tolerance of ₹100 is applied in the UI to prevent floating-point or minor rounding noise from generating false positive discrepancies.
