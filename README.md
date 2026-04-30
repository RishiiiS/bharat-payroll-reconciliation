# Bharat Payroll Reconciliation Tool

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

1. Data is cleaned and normalized
2. Worker identities are resolved
3. Expected pay is computed using wage rules
4. Bank transfers are matched against shifts
5. Expected and actual payments are reconciled
6. Validation checks ensure correctness
7. Results are visualized in a dashboard

---

## Key Features

* Data normalization for inconsistent inputs
* Worker identity resolution
* Accurate expected pay computation
* Automated reconciliation pipeline
* Validation script for correctness
* Interactive dashboard
* Shift-level drilldown
* Exportable outputs

---

## Why This Matters

Workers are systematically underpaid due to missing payments. This creates financial, compliance, and operational risks.

This system enables faster detection of discrepancies, accurate reporting, and reliable payroll operations.

---

## Project Structure

```
bharat-payroll-reconciliation/
│
├── backend/
├── frontend/
├── data/
├── docs/
│
├── production_pipeline.py
├── validate_pipeline.py
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd bharat-payroll-reconciliation
```

---

### 2. Setup backend

```bash
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

### 3. Setup frontend

```bash
cd frontend
npm install
cd ..
```

---

## Running the System

### Step 1: Run pipeline

```bash
python backend/financial_audit.py
```

---

### Step 2: Validate

```bash
python validate_pipeline.py
```

---

### Step 3: Start backend

```bash
python backend/server.py
```

---

### Step 4: Start frontend

```bash
cd frontend
npm run dev
```

---

## Using the Dashboard

* View discrepancy metrics
* Filter workers by status
* Expand rows for shift-level details
* Identify missing and incorrect payments

---

## Forensics

362 out of 2,617 shifts (~13.8%) are missing corresponding bank transfers.

Total discrepancy: ₹836,831.88
Fixing missing payments resolves ~99.1% of the gap

See `docs/FORENSICS.md` for full analysis.

---

## Design Principles

* No hardcoded values in UI
* Data-driven metrics
* ₹100 tolerance for rounding
* Backend-frontend consistency

---

## Production Note

In production, global metrics should be exposed via backend APIs instead of computed from datasets in the frontend.

---

## Status

The system has been fully validated. Results are mathematically consistent and accurately reflected in the UI.
