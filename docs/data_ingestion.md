# KKBox Raw Data Ingestion

## 1. Overview

Project: SaaS Revenue Intelligence Platform

Source: KKBox WSDM 2018 Churn Prediction

Environment:
- Python 3.13
- DuckDB 2.0.0
- dbt-core 1.11.17
- dbt-duckdb 1.10.1

Status: Local raw ingestion completed

## 2. Architecture

KKBox CSV Files
       |
       v
Python Ingestion Script
       |
       v
Persistent DuckDB Database
       |
       v
Raw Schema
       |
       v
dbt Staging Models (next phase)

Database:
data/saas_revenue.duckdb

## 3. Source Datasets

| Source File | DuckDB Table | Records |
|---|---|---:|
| transactions_v2.csv | raw.transactions_v2 | 1,431,009 |
| members_v3.csv | raw.members_v3 | 6,769,473 |
| train_v2.csv | raw.train_v2 | 970,960 |

Total source records: 9,171,442

user_logs_v2.csv is not ingested into DuckDB
during the MVP raw ingestion phase.

## 4. Ingestion Implementation

Script:
scripts/ingest_kkbox.py

The pipeline:
- Reads local source CSV files.
- Creates the raw database schema.
- Loads original source columns as VARCHAR.
- Adds _source_file metadata.
- Adds _ingested_at metadata.
- Preserves all original source records.
- Performs basic row-count and identifier checks.
- Uses transactions for table-level rollback.

Each source table is replaced on rerun.

This implementation is a full-refresh local pipeline,
not an incremental or CDC pipeline.

## 5. Validation

Script:
scripts/validate_raw_ingestion.py

Source-to-target reconciliation:

| Dataset | CSV Records | DuckDB Records | Status |
|---|---:|---:|---|
| Transactions | 1,431,009 | 1,431,009 | PASS |
| Members | 6,769,473 | 6,769,473 | PASS |
| Churn labels | 970,960 | 970,960 | PASS |

All three datasets passed row-count reconciliation.

Additional checks:
- No missing transaction customer IDs.
- No missing member customer IDs.
- No missing churn-label customer IDs.
- No invalid churn-label values.
- Member customer IDs are unique.
- Churn-label customer IDs are unique.

## 6. Data Preservation

Raw source values are preserved as VARCHAR.

No source transactions are deduplicated,
filtered, or modified during ingestion.

Source metadata columns:
- _source_file
- _ingested_at

Limitations:
- Source-row ordinals are not yet preserved.
- Field-level source/target equality is not
  independently verified.
- Source-file checksums are not yet recorded.

## 7. Data Quality Findings

Transaction profiling identified:
- 21,448 zero-payment records.
- 2,218 nonpositive plan durations.
- 5,106 expiry dates before transaction dates.
- 17,700 same-day expiry records.
- 35,133 cancellation-flagged transactions.

These records remain in the raw layer.

See:
docs/transaction_profiling.md

## 8. Security and Reproducibility

Raw KKBox datasets are excluded from GitHub.

The persistent DuckDB database is also excluded
from version control.

Only scripts, documentation, and configuration
files should be committed.

## 9. Running Locally

Activate the Python environment:

source .venv/bin/activate

Ingest data:

python scripts/ingest_kkbox.py

Validate ingestion:

python scripts/validate_raw_ingestion.py

## 10. Next Steps

- Create dbt source definitions.
- Build staging models.
- Standardize dates and numerical fields.
- Add automated dbt tests.
- Investigate subscription lifecycle anomalies.
- Reconstruct subscription entitlements.
- Build financial reporting marts.
