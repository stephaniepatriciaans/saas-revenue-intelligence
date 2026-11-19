# Phase 3 — Modeling policy and execution runbook

**Status:** Proposed implementation; validate against local full dataset before publication.

## Key modeling disclosures

- The source files represent **transaction records**, not a contractual SaaS ledger.
- One transaction-level candidate interval is `[transaction_date, membership_expire_date)` (expiry exclusive) as an explicit unverified convention.
- Intervals exceeding **450 days** are flagged and excluded from the conservative eligible candidate subset; 450 is a **scenario guardrail**, not a validated KKBox rule. Compare sensitivity at 366, 450, and 730 days.
- `dim_plan` is a proxy of source plan attributes, NOT a verified plan catalog.
- The transaction observation window is **2015-01-01 to 2017-03-31**. Historical customer status is left-censored; future coverage may extend beyond the last transaction date.
- An estimated paid customer-month is classified only when exactly **one eligible paid candidate** covers month-end, **no active unresolved candidates**, and there are no same-day attribute conflicts on that candidate.
- Month-end estimated MRR = `actual_amount_paid × 365.25 / (12 × payment_plan_days)` for that uniquely identified candidate; rounded to TWD cents. **This is a day-normalized scenario**, not an identified contractual charge. It is not necessarily exact for calendar-month plans.
- A month with multiple simultaneously active eligible paid events, or invalid / conflicting active evidence, is **ambiguous** with `estimated_mrr_twd = NULL`. We deliberately don't stack payments.
- Absence of a candidate is `no_observed_coverage`, NOT verified cancellation. `other_coverage_only` includes free/zero-payment and other nonpaid evidence.
- Churn and NRR reported by this package are **conditional modeled estimates among consecutive interpretable states**; they are NOT verified financial churn or company-wide NRR. Ambiguous and other-coverage states are excluded from transition denominators.
- The estimated-paid share and ambiguity counts MUST appear next to financial charts, to avoid presenting incomplete MRR as company total.
- No gross margin is produced: KKBox direct costs are unavailable. Any future margin work must be a labeled scenario.
- Do not use `stg_churn_labels.is_churn` to calculate financial churn. For ML, reconstruct prediction cutoffs and avoid leakage.
- The modeled revenue is not a GAAP accounting revenue-recognition calculation.

## Install package into your repository

1. Back up or commit existing changes first.
2. Unzip and copy the included `saas_revenue/` and `docs/` paths into repository root.
3. Keep existing staging and intermediate models intact; package adds new models only.
4. From `saas_revenue/`: `dbt parse`, `dbt run --select int_coverage_guardrails`, `dbt test --select int_coverage_guardrails`, `dbt run --select +fct_customer_month`, `dbt run --select +mart_monthly_kpis`, `dbt test --select int_coverage_guardrails fct_customer_month fct_mrr_movements mart_monthly_kpis dim_month dim_customer dim_plan`.
5. Inspect `select * from main.mart_monthly_kpis order by month_end limit 10`; review ambiguous counts before using any metrics.
6. Only after local verification, commit and mark Jira stories Done. Record all test results and any performance problems.

## Performance caveat

`fct_customer_month` expands transacting customers across reporting months and performs an interval join over the full 1.43M transaction candidate records. It may use significant memory/time on a laptop. Consider `dbt run --threads 2` and table materialization / pre-aggregation if needed. **No performance validation has been performed in your local environment.**

## Planned next iteration

- Deterministic semantic event keys; duplicate content and same-day tie policy.
- Payment-method / plan-specific pricing convention and calendar-month normalization.
- Tests for month-end transition exclusions and sensitivity analysis on 450-day guardrail.
- Snapshot state reconciliation under conflicting zero-payment extensions.
- Dashboard disclosure and financial-metric confidence labels.


## Retention Observability Policy

Financial churn and NRR are modeled estimates, not verified
contractual subscription metrics.

The current customer-month transition audit identified:

- 783,596 estimated-paid to estimated-paid transitions.
- 91,219 estimated-paid to ambiguous transitions.
- Zero estimated-paid to no-observed-coverage transitions.

In March 2017, only 64.46% of opening modeled paid
customers had interpretable transitions.

Under the provisional reporting policy, churn and NRR
are suppressed (NULL) when the model observes no
paid-to-no-coverage exits.

This does not establish that actual churn was zero
or that actual NRR was 100%.

The expiry-duration guardrail is currently 450 days.
It is an analytical assumption requiring sensitivity
testing and is not an official KKBox billing rule.

Modeled MRR and ARR remain provisional estimates and
must not be represented as observed financial results.


## Financial Sensitivity Analysis — March 2017

A scenario-based analysis recomputed modeled customer-month
coverage and recurring revenue under five expiry-duration
thresholds.

| Days | Paid customers | Ambiguous | MRR (TWD) | MRR change |
|---|---:|---:|---:|---:|
| 90 | 885,655 | 288,718 | 114,780,180.57 | -15.20% |
| 180 | 903,576 | 270,590 | 116,900,258.32 | -13.64% |
| 365 | 954,588 | 219,312 | 123,185,148.70 | -8.99% |
| 450 | 1,047,706 | 126,068 | 135,357,698.47 | Baseline |
| 730 | 1,051,582 | 122,161 | 135,841,997.18 | +0.36% |

### Interpretation

The current 450-day scenario produces approximately
NT$135.36 million in modeled March 2017 MRR.

Reducing the threshold to 365 days lowers the estimate
by approximately NT$12.17 million (8.99%).

Increasing the threshold to 730 days raises estimated
MRR by approximately NT$0.48 million (0.36%).

The 450-day sensitivity scenario reconciled with the
existing dbt KPI mart for all modeled months.

### Limitations

These figures are modeled analytical estimates rather
than observed KKBox contractual revenue.

The analysis quantifies expiry-duration sensitivity
while retaining the current revenue normalization and
customer classification assumptions.

It does not validate the correctness of the 450-day
threshold or compare alternative revenue normalization
methods.

Financial churn and NRR remain suppressed where
subscription exit evidence is insufficient.
