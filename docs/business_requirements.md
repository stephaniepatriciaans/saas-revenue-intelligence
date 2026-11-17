# SaaS Revenue Intelligence Platform

## Business objective
Build a reproducible subscription analytics platform
to measure recurring revenue, customer retention,
customer behavior, and scenario-based profitability.

## Source
KKBox WSDM 2018 churn dataset.

## Business questions
1. Why do customers cancel?
2. Which segments contribute the most revenue?
3. Does a product change improve retention?
4. Can we predict churn within 30 days?
5. What revenue could churn reduction recover?

## MVP
- Subscription lifecycle reconstruction
- MRR, ARR, NRR, customer churn
- Cohort retention
- Scenario-based gross margin
- Two-page Power BI dashboard

## V2
Point-in-time churn prediction and revenue at risk.

## V3
Simulated randomized A/B experiment with
a known injected treatment effect.

## Constraints
- Develop locally with DuckDB and dbt.
- Deploy dbt models to Snowflake.
- Keep raw and synthetic data separate.
- Do not claim assumed costs are actual costs.
- Do not claim KKBox labels prove why users churn.
- Document incomplete or ambiguous source records.

## Success criteria
- Reproducible metric calculations
- Documented fact-table grains
- Automated data quality checks
- Reconciliation of MRR movements
- Clear executive reporting
- Defensible assumptions and limitations
