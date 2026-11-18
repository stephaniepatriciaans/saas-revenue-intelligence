"""Ingest raw KKBox transactions into persistent DuckDB
Preserves source fields as VARCHAR and adds provenance
Does not clean, deduplicate, or filter source records
"""

from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

DB_PATH = DATA_DIR / "saas_revenue.duckdb"
CSV_PATH = RAW_DIR / "transactions_v2.csv"

# KKBox source files
CSV_PATH = RAW_DIR / "transactions_v2.csv"
MEMBERS_CSV_PATH = RAW_DIR / "members_v3.csv"
TRAIN_CSV_PATH = RAW_DIR / "train_v2.csv"

EXPECTED_ROWS = 1_431_009


def sql_literal(value: str) -> str:
    """Escape a Python string as a SQL string literal."""
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    if not CSV_PATH.is_file():
        raise FileNotFoundError(
            f"Source file not found: {CSV_PATH}"
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("KKBOX RAW DATA INGESTION")
    print("=" * 60)
    print(f"Source: {CSV_PATH.name}")
    print(f"Database: {DB_PATH}")

    con = duckdb.connect(str(DB_PATH))

    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")

        csv_sql = sql_literal(str(CSV_PATH))
        source_sql = sql_literal(CSV_PATH.name)

        # Atomic replacement: either the full table is
        # committed or the previous version is retained.
        con.execute("BEGIN TRANSACTION")

        try:
            con.execute(
                f"""
                CREATE OR REPLACE TABLE
                    raw.transactions_v2 AS

                SELECT
                    *,
                    {source_sql}::VARCHAR
                        AS _source_file,
                    CURRENT_TIMESTAMP
                        AS _ingested_at

                FROM read_csv(
                    {csv_sql},
                    header = true,
                    all_varchar = true
                )
                """
            )

            result = con.execute(
                """
                SELECT
                    COUNT(*) AS loaded_rows,
                    COUNT(*) FILTER (
                        WHERE msno IS NULL
                           OR TRIM(msno) = ''
                    ) AS missing_customer_ids,
                    COUNT(DISTINCT _source_file)
                        AS distinct_source_files
                FROM raw.transactions_v2
                """
            ).fetchone()

            if result is None:
                raise RuntimeError(
                    "Ingestion validation returned no rows."
                )

            loaded_rows, missing_ids, source_count = result

            if loaded_rows != EXPECTED_ROWS:
                raise RuntimeError(
                    "Row count mismatch: "
                    f"expected {EXPECTED_ROWS:,}, "
                    f"loaded {loaded_rows:,}"
                )

            if missing_ids != 0:
                raise RuntimeError(
                    f"Missing customer IDs: {missing_ids}"
                )

            if source_count != 1:
                raise RuntimeError(
                    "Unexpected source file count."
                )

            con.execute("COMMIT")

        except Exception:
            con.execute("ROLLBACK")
            raise

        print("\nINGESTION VALIDATION")
        print(f"Expected rows: {EXPECTED_ROWS:,}")
        print(f"Loaded rows: {loaded_rows:,}")
        print(f"Missing customer IDs: {missing_ids}")
        print(f"Distinct source files: {source_count}")

        print("\nRaw transaction ingestion passed")
        
    
        # --------------------------------------------------
        # INGEST MEMBERS
        # --------------------------------------------------

        if not MEMBERS_CSV_PATH.is_file():
            raise FileNotFoundError(
                f"Members source not found: {MEMBERS_CSV_PATH}"
            )

        print("\nINGESTING CUSTOMER DEMOGRAPHICS")

        members_path_sql = sql_literal(
            str(MEMBERS_CSV_PATH)
        )
        members_source_sql = sql_literal(
            MEMBERS_CSV_PATH.name
        )

        # Members are loaded separately from transactions.
        # Source fields remain VARCHAR at the raw layer.
        con.execute("BEGIN TRANSACTION")

        try:
            con.execute(
                f"""
                CREATE OR REPLACE TABLE raw.members_v3 AS
                SELECT
                    *,
                    {members_source_sql}::VARCHAR
                        AS _source_file,
                    CURRENT_TIMESTAMP
                        AS _ingested_at
                FROM read_csv(
                    {members_path_sql},
                    header = true,
                    all_varchar = true
                )
                """
            )

            members_result = con.execute(
                """
                SELECT
                    COUNT(*) AS loaded_rows,
                    COUNT(*) FILTER (
                        WHERE msno IS NULL
                           OR TRIM(msno) = ''
                    ) AS missing_customer_ids,
                    COUNT(DISTINCT msno)
                        AS unique_customers
                FROM raw.members_v3
                """
            ).fetchone()

            if members_result is None:
                raise RuntimeError(
                    "Members ingestion validation failed."
                )

            (
                members_rows,
                members_missing_ids,
                members_unique_customers,
            ) = members_result

            if members_rows == 0:
                raise RuntimeError(
                    "Members table is unexpectedly empty."
                )

            if members_missing_ids != 0:
                raise RuntimeError(
                    "Members contains missing customer IDs."
                )

            con.execute("COMMIT")

        except Exception:
            con.execute("ROLLBACK")
            raise

        print("\nMEMBERS INGESTION VALIDATION")
        print(f"Loaded rows: {members_rows:,}")
        print(
            "Unique customers: "
            f"{members_unique_customers:,}"
        )
        print(
            "Missing customer IDs: "
            f"{members_missing_ids:,}"
        )
        print("\nRaw members ingestion passed")
    
        # --------------------------------------------------
        # INGEST CHURN LABELS
        # --------------------------------------------------

        if not TRAIN_CSV_PATH.is_file():
            raise FileNotFoundError(
                f"Churn labels source not found: {TRAIN_CSV_PATH}"
            )

        print("\nINGESTING CHURN LABELS")

        train_path_sql = sql_literal(str(TRAIN_CSV_PATH))
        train_source_sql = sql_literal(TRAIN_CSV_PATH.name)

        con.execute("BEGIN TRANSACTION")

        try:
            con.execute(
                f"""
                CREATE OR REPLACE TABLE raw.train_v2 AS
                SELECT
                    *,
                    {train_source_sql}::VARCHAR
                        AS _source_file,
                    CURRENT_TIMESTAMP
                        AS _ingested_at
                FROM read_csv(
                    {train_path_sql},
                    header = true,
                    all_varchar = true
                )
                """
            )

            train_result = con.execute(
                """
                SELECT
                    COUNT(*) AS loaded_rows,
                    COUNT(DISTINCT msno)
                        AS unique_customers,
                    COUNT(*) FILTER (
                        WHERE msno IS NULL
                           OR TRIM(msno) = ''
                    ) AS missing_customer_ids,
                    COUNT(*) FILTER (
                        WHERE is_churn NOT IN ('0', '1')
                           OR is_churn IS NULL
                    ) AS invalid_churn_labels,
                    COUNT(*) FILTER (
                        WHERE is_churn = '1'
                    ) AS churn_positive,
                    COUNT(*) FILTER (
                        WHERE is_churn = '0'
                    ) AS churn_negative
                FROM raw.train_v2
                """
            ).fetchone()

            if train_result is None:
                raise RuntimeError(
                    "Churn-label validation returned no rows."
                )

            (
                train_rows,
                train_unique_customers,
                train_missing_ids,
                train_invalid_labels,
                train_positive,
                train_negative,
            ) = train_result

            if train_rows == 0:
                raise RuntimeError(
                    "Churn-label table is empty."
                )

            if train_missing_ids != 0:
                raise RuntimeError(
                    "Churn labels contain missing customer IDs."
                )

            if train_invalid_labels != 0:
                raise RuntimeError(
                    "Invalid churn labels detected."
                )

            con.execute("COMMIT")

        except Exception:
            con.execute("ROLLBACK")
            raise

        print("\nCHURN LABEL INGESTION VALIDATION")
        print(f"Loaded rows: {train_rows:,}")
        print(
            f"Unique customers: {train_unique_customers:,}"
        )
        print(f"Missing customer IDs: {train_missing_ids:,}")
        print(f"Invalid churn labels: {train_invalid_labels:,}")
        print(f"Churn-positive records: {train_positive:,}")
        print(f"Churn-negative records: {train_negative:,}")

        print("\nRaw churn-label ingestion passed")



    finally:
        con.close()


if __name__ == "__main__":
    main()
