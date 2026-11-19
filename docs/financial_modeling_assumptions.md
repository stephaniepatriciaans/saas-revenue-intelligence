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



## Revenue Normalization Sensitivity

The baseline monthly revenue normalization uses:

MRR = actual_amount_paid × 365.25 / (12 × payment_plan_days)

Alternative annualization conventions were evaluated using
aggregate proportional rescaling of the existing modeled MRR.

### March 2017 Results

| Convention | Modeled MRR (TWD) | Modeled ARR (TWD) | MRR change |
|---|---:|---:|---:|
| 360-day year | 133,412,105.27 | 1,600,945,263.22 | -1.4374% |
| 365-day year | 135,265,051.17 | 1,623,180,614.10 | -0.0684% |
| 365.25-day year | 135,357,698.47 | 1,624,292,381.64 | Baseline |

### Comparison With Expiry-Duration Sensitivity

The 365-day expiry threshold reduced March modeled MRR
by approximately 8.99% compared with the 450-day threshold.

Using a 360-day annualization convention reduced modeled
MRR by approximately 1.44% compared with 365.25 days.

Within the evaluated scenarios, the expiry-duration
assumption therefore had a larger impact on modeled MRR
than the annualization convention.

### Limitations

These results are analytical estimates, not verified
KKBox contractual recurring revenue.

The normalization comparison uses aggregate proportional
rescaling, rather than recalculating and rounding every
customer-month individually.

The expiry-duration comparisons retain the baseline
normalization and customer classification conventions.

Financial churn and NRR remain unavailable where
subscription exit evidence is insufficient.
