# DECISIONS.md

## 1. Stack Choice

### Python + Pandas

The core problem is data-heavy, not UI-heavy. Most of the complexity lies in:

* cleaning inconsistent data
* handling edge cases
* performing reconciliation and aggregation

Pandas was chosen because it allows:

* fast iteration over messy datasets
* flexible transformations
* easy debugging during exploration

---

### Modular Python Scripts (instead of a monolith)

The pipeline is split into:

* `clean_data.py`
* `match_workers.py`
* `production_pipeline.py`
* `reconcile.py`
* `financial_audit.py`

This separation makes it easier to:

* test each stage independently
* isolate bugs (e.g., matching vs wage logic)
* reason about failures

---

### Local-first execution

The tool runs entirely locally:

* no database
* no external services

This was intentional to:

* reduce setup complexity
* focus on correctness of logic
* make it easy to run and verify

---

### No heavy frontend

A minimal or no UI approach was chosen.

Reason:

* the assignment emphasizes reconciliation and reasoning
* UI would not add much value compared to improving data accuracy

Instead:

* outputs are exported as CSV
* results are readable and structured for ops teams

---

## 2. Worker Matching Strategy

### Primary: Phone Number

Phone number was used as the primary identifier because:

* it is the most stable field across datasets
* names are inconsistent and unreliable

---

### Fallback: Fuzzy Name Matching

Used when phone match fails:

* implemented using token-based similarity
* threshold-based confidence scoring

---

### Tradeoff

This approach favors:

* **precision over recall**

Meaning:

* ambiguous matches are flagged instead of forced

---

## 3. Wage Rate Handling

### Effective-dated lookup

Rates are selected based on:

* role
* state
* seniority
* shift date

---

### Handling overlaps

Instead of resolving overlaps automatically:

* they are flagged for manual review

Reason:

* silently choosing one rate could introduce incorrect payouts
* better to surface ambiguity than hide it

---

## 4. Reconciliation Design

### Worker-level aggregation

Reconciliation is done at worker level instead of per shift because:

* bank transfers are not guaranteed to align perfectly with shifts
* aggregation reduces noise and highlights systemic issues

---

### Tolerance-based matching

Instead of strict equality:

* a tolerance of ₹100 is used

Reason:

* avoids false mismatches due to rounding or minor variations

---

## 5. Audit & Simulation Layer

A separate financial audit layer was added to:

* break down discrepancy into root causes
* simulate corrections (e.g., missing payments)

This was not strictly required but was added to:

* validate hypotheses
* quantify impact

---

## 6. Things I Got Wrong on Purpose

### 1. Did not resolve wage rate overlaps automatically

I chose not to implement a rule to pick one rate in overlapping cases.

Why:

* any automatic choice could be incorrect
* forcing a decision would hide a real data issue

Impact:

* requires manual review for those cases

---

### 2. Did not build a full UI

A full frontend could have been built, but I chose not to.

Why:

* time was better spent improving reconciliation accuracy
* core value lies in analysis, not presentation

Impact:

* usability for non-technical users is limited

---

### 3. Assumed phone numbers uniquely identify workers

This assumption simplifies matching but may not always hold:

* shared phones
* number changes over time

Why kept:

* works well for majority of cases
* flagged ambiguous cases instead of forcing matches

Impact:

* small risk of incorrect mapping in edge cases

---

## 7. What I Would Do With More Time

* Introduce a persistent database (PostgreSQL)
* Track historical worker identities (versioned records)
* Build a lightweight UI for ops teams
* Add automated anomaly detection alerts
* Integrate reconciliation checks into upstream pipeline

---

## 8. Summary

The system prioritizes:

* correctness over convenience
* transparency over silent assumptions
* auditability over automation

Tradeoffs were made intentionally to ensure that:

> any uncertainty is surfaced, not hidden.
