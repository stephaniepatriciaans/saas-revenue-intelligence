# SaaS Revenue Intelligence Platform

An analytics engineering project that rebuilds subscription revenue metrics (MRR, ARR, cohort retention) from raw, messy transaction data. The pipeline uses Python, DuckDB and dbt.

The source data is the public **KKBox WSDM 2018** music-streaming churn dataset. It is a log of billing transactions, not a clean subscription ledger. The core challenge is turning those transactions into defensible month-end subscription metrics **without overcounting revenue or hiding ambiguity**.

> **Status:** Phase 3 of 7 complete. Ingestion, staging, intermediate and mart layers are built and tested locally. Dashboards, churn prediction, experimentation and CI/CD are planned next (see [Roadmap](#roadmap)).

---

## Business questions

1. Which customer segments contribute the most recurring revenue?
2. How does retention evolve across acquisition cohorts?
3. Can we predict customer churn within 30 days? *(Phase 5)*
4. Does a product change improve retention? *(Phase 6, simulated A/B test)*
5. How much revenue could churn reduction recover?

---

## Architecture

```
KKBox CSVs ──► Python ingestion ──► DuckDB (raw schema)
                                        │
                                        ▼
                                 dbt staging models
                                        │
                                        ▼
                      dbt intermediate models (quality + coverage)
                                        │
                                        ▼
                      dbt marts (dimensions, facts, KPI mart)
```

| Layer | Models | Purpose |
|---|---|---|
| **Raw** | `raw.transactions_v2`, `raw.members_v3`, `raw.train_v2` | Original source values kept as VARCHAR, with `_source_file` and `_ingested_at` provenance |
| **Staging** | `stg_transactions`, `stg_members`, `stg_churn_labels` | Type casting and standardization, with row counts matched to raw |
| **Intermediate** | `int_transaction_eligibility`, `int_transaction_day_conflicts`, `int_subscription_cross_date_overlaps`, `int_subscription_coverage_candidates`, `int_coverage_guardrails` | Classify each transaction's revenue eligibility, detect same-day conflicts and cross-date overlaps, and build candidate coverage intervals |
| **Marts** | `dim_customer`, `dim_plan`, `dim_month`, `fct_transactions`, `fct_customer_month`, `fct_mrr_movements`, `fct_cohort_retention`, `mart_monthly_kpis` | Month-end customer status, MRR movements, cohort retention and monthly KPIs |

---

## Data

| Source file | Records |
|---|---:|
| `transactions_v2.csv` | 1,431,009 |
| `members_v3.csv` | 6,769,473 |
| `train_v2.csv` | 970,960 |
| **Total** | **9,171,442** |

All three tables match the source files' row counts exactly after ingestion. Raw data and the DuckDB database are excluded from version control.

**Key data quality findings** (see [`docs/transaction_profiling.md`](docs/transaction_profiling.md)):

- 21,448 zero-payment transactions
- 2,218 nonpositive plan durations
- 5,106 records whose expiry date is before the transaction date
- 27,942 customer-days with multiple transactions
- 192,279 customer-days with potential coverage overlap, across 127,929 customers

---

## Modeling approach

**MRR is not the sum of payments.** Payments include renewals, prepaid plans and possibly simultaneous events, so adding them up overcounts revenue. Instead:

- Each transaction defines a candidate coverage interval `[transaction_date, membership_expire_date)`.
- A customer-month counts as **estimated paid** only when exactly **one eligible paid candidate** covers month-end and there are no unresolved conflicts.
- Estimated MRR = `actual_amount_paid × 365.25 / (12 × payment_plan_days)`.
- Months with conflicting or overlapping paid evidence are classified **ambiguous**, with `estimated_mrr = NULL`. Payments are never stacked.
- A missing candidate is classified `no_observed_coverage`, not a confirmed cancellation.
- ARR = 12 × month-end MRR.

Full policy: [`docs/subscription_entitlement_policy.md`](docs/subscription_entitlement_policy.md) · [`docs/financial_modeling_assumptions.md`](docs/financial_modeling_assumptions.md)

---

## Sensitivity analysis

Modeled MRR for March 2017 under different expiry-duration guardrails:

| Expiry guardrail | Estimated paid customers | Modeled MRR (TWD) |
|---|---:|---:|
| 90 days | 885,655 | 114.8M |
| 180 days | 903,576 | 116.9M |
| 365 days | 954,588 | 123.2M |
| **450 days (baseline)** | **1,047,706** | **135.4M** |
| 730 days | 1,051,582 | 135.8M |

- The results level off above 450 days: going from 450 to 730 days changes modeled MRR by only about 0.4%.
- The expiry guardrail has a much larger effect than the annualization convention. Using a 360-day year instead of 365.25 days changes MRR by about 1.4%.

---

## Testing

- **16 custom dbt tests** covering:
  - row counts matched between raw and staging
  - unique grain at each level (transaction-day, customer-month, cross-date overlap)
  - eligibility and conflict rules
  - coverage-candidate reconciliation
  - MRR movement arithmetic
  - KPI bounds
  - retention observability
- Column tests (`not_null`, `unique`, `accepted_values`) in each layer's YAML files
- Python unit tests for the metric formulas in [`scripts/validate_metric_contract.py`](scripts/validate_metric_contract.py)

---

## Limitations

- KKBox did not publish contracts, billing policies, refunds or cost data. **All MRR, ARR and retention figures are modeled estimates**, not verified financial results or GAAP revenue.
- The model currently finds no estimated-paid to no-coverage transitions. Because of that, **churn and NRR are suppressed (NULL)** rather than reported as 0% or 100%.
- The 450-day guardrail is an analytical assumption, not a KKBox rule.
- Competition churn labels (`is_churn`) are not used for financial churn.
- No gross margin is reported, because no cost data is available.

---

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Business requirements, metric contracts, data model design | ✅ Done |
| 2 | Raw ingestion, source profiling, dbt staging | ✅ Done |
| 3 | Intermediate quality models, revenue marts, sensitivity analysis | ✅ Done |
| 4 | Power BI executive dashboards | ⏳ Planned |
| 5 | Point-in-time churn prediction and revenue at risk | ⏳ Planned |
| 6 | Simulated A/B experiment with a known injected effect | ⏳ Planned |
| 7 | CI/CD, automation and Snowflake deployment | ⏳ Planned |

The project runs as Scrum with a Jira backlog: [`docs/jira_backlog.md`](docs/jira_backlog.md).

---

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Place KKBox CSVs in data/raw/ (download from Kaggle: WSDM - KKBox's Churn Prediction Challenge)
python scripts/ingest_kkbox.py
python scripts/validate_raw_ingestion.py

cd saas_revenue
dbt build
```

**Stack:** Python 3.13 · DuckDB · dbt-core 1.11 · dbt-duckdb 1.10
