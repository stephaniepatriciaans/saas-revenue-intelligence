# Data Quality Contract — Version 1.0

Project: SaaS Revenue Intelligence Platform

Dataset: KKBox WSDM 2018

Status: Proposed — pending source profiling

## 1. Source Data Requirements

### raw_members

Expected fields:
- msno
- city
- bd
- gender
- registered_via
- registration_init_time

Rules:
- msno must not be null.
- Duplicate customer IDs must be investigated.
- Age values must be profiled for invalid values.
- Missing demographic attributes are permitted.
- Source file version must be preserved.

### raw_transactions

Expected fields:
- msno
- payment_method_id
- payment_plan_days
- plan_list_price
- actual_amount_paid
- is_auto_renew
- transaction_date
- membership_expire_date
- is_cancel

Rules:
- msno must not be null.
- payment_plan_days must be evaluated for
  zero, negative, and unusual values.
- Negative or zero payments must be flagged.
- Transaction dates must be valid.
- Expiry dates must be valid.
- Cancellation flags must have valid values.
- Identical-looking transactions must not
  be automatically deleted.
- Source file and row provenance must be stored.

### raw_user_logs

Expected fields:
- msno
- date
- num_25
- num_50
- num_75
- num_985
- num_100
- num_unq
- total_secs

Rules:
- msno must not be null.
- Activity dates must be valid.
- Listening counts must be nonnegative.
- total_secs must be nonnegative.
- Missing or unusual activity must be profiled.
- Do not require one row per customer per day
  until source uniqueness has been verified.

### raw_churn_labels

Rules:
- Customer IDs must not be null.
- Churn labels must be 0 or 1.
- Prediction cohort must be identified.
- Duplicate customer-cohort labels must fail.
- Labels must not enter financial marts.
- Labels must not enter predictive features.

## 2. Staging Model Requirements

All staging models must:

- Use explicit data types.
- Standardize field names.
- Preserve source identifiers.
- Preserve source version.
- Document invalid and missing values.
- Avoid destructive deduplication.
- Avoid business metric aggregation.

Expected staging models:
- stg_members
- stg_transactions
- stg_user_logs
- stg_churn_labels

## 3. Subscription Lifecycle Requirements

### int_subscription_events

Rules:
- Every event must have a traceable source.
- Transaction ordering must be deterministic.
- Cancellation flags must not automatically
  terminate paid entitlement.
- Ambiguous ordering must be flagged.

### int_subscription_entitlements

Rules:
- Valid intervals must have positive duration.
- Active entitlement intervals must not
  conflict after reconstruction.
- Overlapping transactions must be resolved
  according to documented business rules.
- Unknown entitlement states must be flagged.
- Entitlements must respect reporting boundaries.

### int_customer_month_status

Rules:
- One customer per reporting month.
- Customer ID must not be null.
- Month key must not be null.
- Paid status must use reconstructed entitlement.
- MRR must be nonnegative.
- Incomplete reporting periods must be flagged.

## 4. Financial Mart Requirements

### fct_customer_month

Required tests:
- Unique customer_id + month_key.
- Not-null customer_id.
- Not-null month_key.
- Nonnegative beginning_mrr.
- Nonnegative ending_mrr.
- Valid active-status indicators.
- Consistent churn classification.

### fct_mrr_movements

Required tests:
- Unique customer_id + month_key.
- Nonnegative movement components.
- Mutually exclusive movement classifications.
- Correct classification of new vs reactivated.
- Monthly MRR reconciliation.

Reconciliation equation:

ending_mrr =
  beginning_mrr
  + new_mrr
  + reactivation_mrr
  + expansion_mrr
  - contraction_mrr
  - churned_mrr

### fct_cohort_retention

Required tests:
- Unique cohort_month + cohort_age.
- Cohort size must be positive.
- Active customers cannot exceed cohort size.
- Retention rate must be between 0 and 1.
- Cohort age must be nonnegative.
- Incomplete cohort observations must be flagged.

## 5. Scenario Model Requirements

Assumed financial measures must:

- Be stored separately from observed measures.
- Contain explicit scenario identifiers.
- Specify the assumed cost rate.
- Identify all synthetic input values.
- Never be labeled actual company costs.
- Never overwrite observed transactions.

## 6. Test Severity

ERROR:
- Duplicate primary keys in reporting marts.
- Missing required identifiers.
- Negative final MRR.
- Broken financial reconciliation.
- Invalid published reporting dates.
- Revenue double-counting.

WARN:
- Missing optional demographics.
- Unusual source transaction patterns.
- Zero or negative source payment records.
- Ambiguous subscription histories.
- Unexpected listening activity.

Warning records must be investigated.

A warning must not silently become a valid
financial entitlement.

## 7. Validation Policy

All critical financial tests must pass before
a reporting mart is considered publishable.

Known unresolved source limitations must be
documented in the README.

No model may claim validated financial accuracy
until tested against the loaded source data.
