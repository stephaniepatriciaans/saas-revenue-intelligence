# KKBox Transaction Data Profiling

## 1. Overview

Project: SaaS Revenue Intelligence Platform

Source: KKBox WSDM 2018 Churn Prediction
Dataset: transactions_v2.csv
Currency: TWD
Profiling tool: Python + DuckDB

Status: Source profiling completed

All statistics below are observed from the source
dataset, not synthetic or assumed.

## 2. Dataset Summary

| Metric | Value |
|---|---:|
| Total transactions | 1,431,009 |
| Unique customers | 1,197,050 |
| Average transactions/customer | 1.20 |
| Null customer IDs | 0 |
| Exact duplicate groups | 0 |
| Extra exact duplicate rows | 0 |

## 3. Completeness

All nine transaction fields had zero missing values
under the NULL, empty-string, and whitespace checks.

All tested numeric fields converted successfully.

These results do not establish complete semantic
or financial validity.

## 4. Payment and Plan Findings

| Finding | Count |
|---|---:|
| Zero payments | 21,448 |
| Negative payments | 0 |
| Payments below list price | 9,639 |
| Payments above list price | 2,264 |
| Nonpositive plan durations | 2,218 |
| Invalid numeric conversions | 0 |

Minimum payment: 0 TWD
Maximum payment: 2,000 TWD

Minimum plan duration: 0 days
Maximum plan duration: 450 days

These categories may overlap.

Zero payments and unusual pricing must be classified
before calculating recurring revenue.

## 5. Date and Expiry Findings

| Finding | Count |
|---|---:|
| Invalid transaction dates | 0 |
| Invalid expiry dates | 0 |
| Expiry before transaction | 5,106 |
| Expiry same day | 17,700 |
| Expiry after transaction | 1,408,203 |

Transaction date range:
2015-01-01 through 2017-03-31

Membership expiry date range:
2016-04-19 through 2036-10-15

Expiry dates cannot be assumed to equal transaction
dates plus payment_plan_days.

Unusual entitlement histories require investigation.

## 6. Cancellation and Auto-Renewal

| Finding | Count |
|---|---:|
| Not cancellation-flagged | 1,395,876 |
| Cancellation-flagged | 35,133 |
| Auto-renew off | 307,234 |
| Auto-renew on | 1,123,775 |
| Invalid cancellation flags | 0 |
| Invalid auto-renew flags | 0 |
| Cancellation and auto-renew on | 35,133 |
| Cancellation and auto-renew off | 0 |

All cancellation-flagged transaction records have
auto-renew enabled in this source dataset.

The business explanation is not established.

Transaction-level cancellation flags must not be
used directly as customer-level financial churn.

## 7. Implications for Financial Modeling

1. Preserve original source transactions.
2. Do not automatically deduplicate billing events.
3. Keep source payments separate from calculated MRR.
4. Flag zero payments and invalid plan durations.
5. Reconstruct subscription entitlements before
   calculating customer-month MRR.
6. Investigate abnormal expiry dates.
7. Do not equate is_cancel with customer churn.
8. Restrict reporting to documented observation
   windows supported by source evidence.
9. Validate MRR movements before publication.
10. Keep financial observations separate from
    assumed cost and synthetic experiment data.

## 8. Limitations

- Source data does not establish cancellation causes.
- No verified customer-level cost data is available.
- Exact row uniqueness does not prove billing validity.
- Some source subscription histories are ambiguous.
- Financial MRR has not yet been calculated.
- No raw database ingestion has been completed.

## 9. Next Steps

- Implement raw DuckDB ingestion.
- Preserve row counts and source provenance.
- Validate ingestion reconciliation.
- Build dbt staging models.
- Investigate subscription lifecycle anomalies.
