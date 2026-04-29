# Bharat Payroll Reconciliation Tool

## Overview

This project reconstructs expected wages for field workers and reconciles them against actual bank transfers to identify discrepancies such as underpayment, overpayment, and missing payments.

It is designed as a lightweight, local-first tool for ops and finance teams to audit payroll pipelines.

---

## Key Features

* Data cleaning and normalization (phones, timestamps, wage rates)
* Worker matching (exact + fuzzy fallback)
* Expected pay calculation using effective-dated wage rules
* Reconciliation of expected vs actual payments
* Financial audit with:

  * discrepancy breakdown
  * root cause attribution
  * simulation of missing payments
* Flags for manual review with reasons

---

## Project Structure

```
bharat-payroll-reconciliation/
│
├── backend/
│   ├── clean_data.py
│   ├── match_workers.py
│   ├── reconcile.py
│   ├── financial_audit.py
│   └── production_pipeline.py
│
├── data/
│   ├── supervisor_logs.csv
│   ├── bank_transfers.csv
│   ├── wage_rates.csv
│   ├── workers.csv
│   └── financial_audit_results.csv
│
├── FORENSICS.md
├── README.md
├── DECISIONS.md
├── ASSUMPTIONS.md
└── AI_USAGE.md
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd bharat-payroll-reconciliation
```

---

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Pipeline

### Step 1: Run full production pipeline

```bash
python backend/production_pipeline.py
```

This performs:

* data cleaning
* worker matching
* expected pay calculation
* reconciliation

---

### Step 2: Run financial audit

```bash
python backend/financial_audit.py
```

This generates:

* discrepancy breakdown
* root cause analysis
* simulation results

Output:

```
data/financial_audit_results.csv
```

---

## Output

The final output includes:

* Worker-level reconciliation
* Discrepancy classification
* Audit breakdown (missing vs incorrect payments)
* Corrected simulation values

---

## Key Insight

The system identifies that:

> ~12% of valid shifts are not converted into bank payments, accounting for ~99% of the total discrepancy.

See `FORENSICS.md` for full analysis.

---

## Notes

* The system uses phone numbers as primary identity keys
* Uncertain matches and anomalous records are flagged for manual review
* Untrusted data (e.g., invalid shifts) is excluded from financial conclusions

---

## Next Steps (Optional)

* Add UI for ops team review
* Integrate database for persistence
* Add automated validation checks in upstream systems
