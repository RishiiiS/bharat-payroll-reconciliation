# ASSUMPTIONS.md

## Overview

This project required working with incomplete and inconsistent data across multiple systems.
Several assumptions were necessary to reconstruct expected pay and reconcile it with actual payments.

These assumptions are listed below and ranked by **risk** — i.e., how wrong the final conclusions could be if the assumption does not hold.

---

## High-Risk Assumptions

### 1. Each bank transfer corresponds to a single shift

**Assumption:**
One bank transfer = one shift payment.

**Why it matters:**
This directly affects reconciliation logic. If payments are actually:

* batched (weekly/daily), or
* aggregated across multiple shifts

then comparing counts (payments vs shifts) becomes invalid.

**Evidence supporting it:**

* Average payment amount ≈ average expected per shift
* Payment distribution closely matches shift-level pay

**Risk if wrong:**
Very high — would invalidate the “missing payments” conclusion.

---

### 2. Supervisor logs represent ground truth for work performed

**Assumption:**
All valid work done by workers is captured in `supervisor_logs.csv`.

**Why it matters:**
Expected pay is entirely derived from these logs.

**Risks:**

* Missing logs → underestimation of expected pay
* Duplicate logs → overestimation

**Mitigation:**

* Basic sanity checks applied
* obvious anomalies (e.g., 450-hour shift) flagged

**Risk if wrong:**
Very high — affects entire discrepancy calculation.

---

### 3. Phone number uniquely identifies a worker

**Assumption:**
Each phone number maps to exactly one worker.

**Why it matters:**
Worker matching relies heavily on phone normalization.

**Risks:**

* shared devices (common in rural settings)
* number changes over time
* recycled numbers

**Mitigation:**

* fuzzy name matching fallback
* ambiguous matches flagged

**Risk if wrong:**
High — could misattribute payments and distort reconciliation.

---

## Medium-Risk Assumptions

### 4. Wage rates are correctly defined in the source data

**Assumption:**
The `wage_rates.csv` file reflects correct pay rules.

**Issue observed:**

* overlapping effective date ranges

**Handling:**

* overlaps flagged instead of resolved

**Risk if wrong:**
Medium — affects correctness of expected pay for some shifts.

---

### 5. Timezone normalization is accurate

**Assumption:**
All timestamps, once converted to UTC, correctly represent actual shift dates.

**Why it matters:**

* wage rate selection depends on shift date

**Risk if wrong:**
Medium — could assign wrong rate to a shift.

---

### 6. Hours reported in logs are accurate

**Assumption:**
The `hours` field represents actual worked duration.

**Issue observed:**

* extreme outlier (450-hour shift)

**Handling:**

* unrealistic values flagged and excluded

**Risk if wrong:**
Medium — could skew expected pay.

---

## Low-Risk Assumptions

### 7. Bank transfer data is complete for the given time range

**Assumption:**
All payments within the stated period are present in `bank_transfers.csv`.

**Evidence:**

* date ranges match exactly with logs

**Remaining uncertainty:**

* individual missing entries still possible (and observed)

**Risk if wrong:**
Low to medium — already partially captured by discrepancy analysis.

---

### 8. Minor rounding differences are acceptable

**Assumption:**
Small differences (±₹100) are not meaningful discrepancies.

**Why:**

* rounding
* paise to rupee conversion
* system precision differences

**Risk if wrong:**
Low — does not affect systemic conclusions.

---

## Questions I Would Have Asked

If this were a real system, the following clarifications would be critical:

1. Are bank payments strictly one-to-one with shifts?
2. Can payments be batched or delayed?
3. How are wage rates updated and validated?
4. Are supervisor logs audited or verified?
5. Can workers change phone numbers over time?
6. What guarantees exist in the payment pipeline (retry logic, failure handling)?

---

## Summary

The highest-risk assumptions relate to:

* mapping shifts to payments
* correctness of source logs
* worker identity resolution

Despite these uncertainties, multiple independent signals (counts, distributions, simulation) point to the same conclusion:

> The discrepancy is primarily driven by missing payment entries rather than calculation errors.

This consistency increases confidence in the findings, even under imperfect assumptions.
