# AI_USAGE.md

## Overview

AI tools were used throughout this project to accelerate development, especially in boilerplate generation, structuring the pipeline, and refining documentation. However, most of the critical logic, debugging, and reasoning required manual intervention and verification.

---

## Where AI Helped

### 1. Initial Project Structuring

AI was useful in:

* suggesting a clean modular structure (clean → match → reconcile → audit)
* outlining the overall pipeline
* generating starter code for data loading and transformations

This helped reduce setup time and allowed focus on core logic earlier.

---

### 2. Boilerplate Code

AI was effective for:

* writing repetitive Pandas operations
* generating function scaffolding
* formatting outputs (tables, summaries)

This was especially helpful when implementing:

* validation scripts
* aggregation logic
* debug outputs

---

### 3. Prompt-driven Iteration

AI was used as a fast feedback loop:

* testing different approaches (e.g., matching strategies)
* refining reconciliation logic
* generating validation checks

It helped explore multiple directions quickly.

---

### 4. Documentation Drafting

AI significantly helped in:

* structuring markdown files
* organizing findings clearly
* improving readability of explanations

However, all content was reviewed and edited manually.

---

## Where AI Did NOT Help Much

### 1. Debugging Data Issues

AI struggled with:

* identifying why expected pay values were unrealistic (e.g., ₹2 lakh anomaly)
* reasoning about real-world data inconsistencies

These required:

* manual inspection of outliers
* step-by-step debugging
* understanding domain context

---

### 2. Root Cause Analysis

AI could suggest possibilities, but:

* it did not reliably identify the actual issue (missing payments)
* conclusions required combining multiple signals:

  * counts (payments vs shifts)
  * distributions
  * simulation results

This part was primarily manual reasoning.

---

### 3. Handling Ambiguity

The problem involved:

* incomplete data
* conflicting signals
* real-world inconsistencies

AI often gave:

* overly confident answers
* assumptions without sufficient evidence

These had to be corrected.

---

## Where AI Was Incorrect or Misleading

### 1. Over-simplified Joins

Early suggestions assumed:

* clean joins between datasets

In reality:

* data required normalization and fuzzy matching

---

### 2. Ignoring Edge Cases

AI-generated logic often:

* ignored overlapping wage rates
* assumed perfect timestamps
* did not account for missing data

These had to be explicitly handled.

---

### 3. Overconfident Conclusions

AI sometimes:

* jumped to conclusions (e.g., blaming specific causes without evidence)

This required:

* validating every claim with actual data
* avoiding unsupported assumptions

---

## Corrections Made

To address these issues, I:

* added validation layers at every stage
* introduced manual review flags instead of forcing decisions
* verified outputs using distribution checks and sampling
* built a simulation layer to confirm root causes
* separated trusted vs untrusted data

---

## Final Takeaway

AI was most useful as:

* a productivity tool
* a brainstorming assistant

But not as:

* a source of truth
* a replacement for reasoning

The final solution required:

* careful validation
* iterative debugging
* independent verification of all results

---

## Summary

AI accelerated development, but:

> The correctness of the system depended on manual validation, debugging, and reasoning — especially when dealing with messy, real-world data.

All critical findings were verified independently before being included in the final output.
