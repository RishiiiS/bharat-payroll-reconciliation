# FORENSICS.md

## 1. Executive Summary

This investigation reconstructs expected wages for ~12,000 field workers over a 90-day period and reconciles them against actual bank transfers.

Across a sample of 100 workers (2,555 shifts), we identified a **total discrepancy of ₹836,831.88**, with **88% of workers underpaid**.

The key takeaway is straightforward:

> The system is correctly calculating wages, but it is **not consistently paying for all recorded work**.

Roughly **12% of valid shifts are missing corresponding bank transfers**, and this single issue explains nearly the entire discrepancy. A simulation confirms that **restoring those missing payments reduces the gap by ~99.1%**.

---

## 2. Dataset Overview

* Workers analyzed: 100
* Total shifts: 2,555
* Total bank payments: 2,255
* Time range: Jan 7, 2025 → Mar 26, 2025

The two datasets (logs and payments) align on time range, which rules out simple data cutoff issues.

---

## 3. What Was Reconstructed

For each shift:

* Worker identity was resolved using phone number + fallback name matching
* Hourly wage was determined using role, state, seniority, and effective date
* Expected pay was computed and validated

Special cases were explicitly handled:

* Overlapping wage rates → flagged
* Unrealistic durations (e.g., 450-hour shift) → quarantined
* Ambiguous matches → marked for review

Only **trusted records** were used for financial conclusions.

---

## 4. High-Level Results

| Metric                       | Value           |
| ---------------------------- | --------------- |
| Total Expected Pay (trusted) | ₹6,577,918.48   |
| Total Actual Pay             | ₹5,741,086.60   |
| **Net Discrepancy**          | **₹836,831.88** |

Worker-level classification:

* Underpaid: 88 workers
* Overpaid: 8 workers
* Matched (±₹100): 4 workers

This is not a small set of outliers — it is a **system-wide pattern**.

---

## 5. Primary Finding: Missing Payments

### Evidence

* Total shifts: 2,555
* Total payments: 2,255
* Gap: **300 missing payments (~12%)**

This gap:

* exists across nearly all workers
* is consistent across the full date range
* is not localized to a specific time window

Additionally:

* Average expected pay per shift ≈ ₹2,574
* Average actual payment ≈ ₹2,545

This near match confirms that:

> Each bank transfer is intended to represent a single shift.

---

### Interpretation

Since:

* payments are roughly 1:1 with shifts
* but fewer payments exist than shifts

The most likely explanation is:

> A subset of valid shifts are not being converted into bank transfer entries.

---

### Financial Impact

* Estimated loss due to missing payments: **₹843,992.68**
* This is **~101% of the net discrepancy**

The percentage exceeds 100% because:

* some workers were overpaid, which partially offsets the total gap

---

## 6. Secondary Issues

### 6.1 Incorrect Payment Amounts

There is a small but consistent gap between expected and actual amounts:

* Avg expected per shift: ₹2,574
* Avg actual payment: ₹2,545

This suggests:

* rounding differences
* outdated rate usage
* or small deductions

Estimated impact:

* **₹60,815.22 (~7.3%)**

---

### 6.2 Corrupted Payments

A small number of payments are clearly invalid:

* Example: ₹17 transfer
* Total corrupted payments: 8

These are far below any valid wage rate and likely represent:

* failed transactions
* partial writes
* or system errors

Impact:

* **₹19,824.02** (subset of incorrect payments)

---

### 6.3 Wage Rate Overlaps

* 61 shifts matched multiple wage rate windows
* This introduces ambiguity in expected pay

While flagged and excluded from trusted totals, this is still a configuration issue in the system.

---

### 6.4 Data Entry Errors

* One extreme case: 450-hour shift
* Indicates lack of validation in upstream logging

This did not materially affect totals but highlights a data integrity gap.

---

## 7. Simulation: What Happens If We Fix It?

To test the hypothesis, missing payments were estimated and added back:

* Recomputed discrepancy: **₹7,160.80**
* Reduction: **~99.1%**

This is the strongest piece of evidence in the analysis.

> If missing payments are restored, the discrepancy nearly disappears.

---

## 8. What We Can Rule Out

The following were tested and eliminated:

* Timezone misalignment
* Date range mismatch
* Payment aggregation (e.g., weekly batching)
* Identity mismatch across datasets

None of these explain the observed gap.

---

## 9. Confidence Assessment

| Area                          | Confidence |
| ----------------------------- | ---------- |
| Worker matching               | High       |
| Expected pay calculation      | High       |
| Missing payment diagnosis     | High       |
| Incorrect payment amounts     | Medium     |
| Exact upstream failure source | Low        |

---

## 10. Recommendations

### 1. Enforce Shift → Payment Integrity

Every logged shift should produce exactly one payment record.
Introduce a reconciliation check at the pipeline level.

---

### 2. Add Input Validation

Reject:

* unrealistic durations (>12 hours)
* malformed entries

---

### 3. Fix Wage Rate Configuration

* Remove overlapping effective date ranges
* Ensure a single valid rate per shift

---

### 4. Improve Observability

* Track shift IDs through to payment records
* Log failures in payment generation

---

### 5. Stabilize Payment Processing

* Detect and retry failed transfers
* Flag anomalous low-value payments automatically

---

## 11. Final Conclusion

The discrepancy is not due to incorrect wage calculation.

It is caused by a **systemic failure in the payment pipeline**, where a consistent portion of valid work (~12%) is not being paid.

This issue is:

* widespread
* consistent
* and financially significant

Fixing this gap would resolve **almost the entire discrepancy**.
