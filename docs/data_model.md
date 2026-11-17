# SaaS Revenue Intelligence Platform
## Dimensional Data Model — Draft v1

### 1. Data Source

Dataset: KKBox WSDM 2018 Churn Prediction

Currency: TWD (New Taiwan Dollar)

Main sources:
- members_v3.csv
- transactions.csv / transactions_v2.csv
- user_logs.csv / user_logs_v2.csv
- train.csv / train_v2.csv

The source versions must be tracked explicitly.
Overlapping records across versions must not be
blindly appended or deduplicated.

### 2. Raw Layer

raw_members
Grain: one source membership record

raw_transactions
Grain: one source transaction record

raw_user_logs
Grain: one source daily listening record

raw_churn_labels
Grain: one customer per labeled prediction cohort

Raw records must retain source provenance.

### 3. Staging Layer

stg_members
- customer_id
- city
- age
- gender
- registration_method
- registration_date

stg_transactions
- source_event_key
- customer_id
- payment_method_id
- payment_plan_days
- plan_list_price
- actual_amount_paid
- is_auto_renew
- transaction_date
- membership_expire_date
- is_cancel

stg_user_logs
- customer_id
- activity_date
- num_25
- num_50
- num_75
- num_985
- num_100
- num_unq
- total_secs

stg_churn_labels
- customer_id
- label_cohort
- is_churn

### 4. Intermediate Layer

int_subscription_events
Grain: one ordered source transaction event

Purpose:
- Establish event ordering
- Identify cancellation records
- Identify renewals and plan changes
- Flag invalid and ambiguous records

int_subscription_entitlements
Grain: one reconstructed entitlement interval

Purpose:
- Determine active subscription periods
- Resolve overlap and expiry semantics
- Preserve reconstruction assumptions

int_customer_month_status
Grain: one customer per calendar month

Purpose:
- Determine month-end paid status
- Assign normalized MRR
- Identify customer status transitions

### 5. Dimensional Layer

dim_customer
Grain: one row per customer
Primary key: customer_id

dim_plan
Grain: one distinct observed plan configuration
Primary key: plan_key

dim_month
Grain: one row per calendar month
Primary key: month_key

### 6. Fact Layer

fct_transactions
Grain: one source transaction event

fct_customer_month
Grain: one customer per reporting month

Measures:
- beginning_mrr
- ending_mrr
- is_active_beginning
- is_active_ending
- churn_flag

fct_mrr_movements
Grain: one customer per reporting month

Measures:
- new_mrr
- expansion_mrr
- contraction_mrr
- churned_mrr
- reactivation_mrr

fct_cohort_retention
Grain: one acquisition cohort per cohort age

Measures:
- cohort_size
- active_customers
- retention_rate

### 7. Data Modeling Rules

1. Never aggregate monetary values across
   incompatible grains.

2. Do not use is_cancel directly as the
   financial customer churn indicator.

3. Do not interpret transaction payments
   as MRR without normalization.

4. Reconstruct entitlement periods before
   calculating monthly recurring revenue.

5. Separate observed transaction values
   from assumed costs and synthetic data.

6. Retain source version and event provenance.

7. Document all unresolved subscription
   lifecycle ambiguities.

8. Enforce one row per customer per
   reporting month in fct_customer_month.

9. Reconcile beginning MRR, movements,
   and ending MRR.

10. Do not use future transactions or
    churn labels as historical features.
