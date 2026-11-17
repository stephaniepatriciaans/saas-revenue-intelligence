# Dimensional Model — Draft v1

## Source tables

members:
Customer demographics and membership attributes.

transactions:
Payment, plan duration, auto-renewal,
cancellation, and expiry information.

user_logs:
Customer activity and engagement.
Not required for the MVP financial marts.

train:
Dataset-specific churn labels.
Reserved for V2 validation and modeling.

## Dimensions

dim_customer
Grain: one row per customer.
Primary key: customer_id.

dim_plan
Grain: one row per observed plan configuration.
Primary key: plan_key.

dim_month
Grain: one row per calendar month.
Primary key: month_key.

## Facts

fct_transactions
Grain: one source transaction event.
Key: source_event_key, pending validation.

fct_customer_month
Grain: one customer per reporting month.
Key: customer_id + month_key.

fct_mrr_movements
Grain: one customer per reporting month.
Key: customer_id + month_key.

fct_cohort_retention
Grain: one cohort per age in months.
Key: cohort_month + cohort_age.

## Modeling rules

- No direct summation across mismatched grains.
- Resolve overlapping subscription entitlements.
- Reconcile MRR movements to ending MRR.
- Do not use churn labels as financial churn events.
- Treat historical observation boundaries explicitly.
- Document ambiguous source transactions.
