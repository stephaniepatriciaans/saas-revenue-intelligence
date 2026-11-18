
"""Full KKBox transaction profiling using DuckDB
Source: transactions_v2.csv
All results are calculated from observed KKBox data
"""

from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "transactions_v2.csv"
)


def main() -> None:
    if not CSV_PATH.is_file():
        raise FileNotFoundError(
            f"Transaction file not found: {CSV_PATH}"
        )

    print("=" * 60)
    print("KKBOX FULL TRANSACTION PROFILING")
    print("=" * 60)

    con = duckdb.connect(database=":memory:")

    try:
        # Keep the source identifiers and date strings intact
        # No persistent database tables are created here
        # Safely register the CSV path as a SQL string literal
        csv_path_sql = "'" + str(CSV_PATH).replace("'", "''") + "'"

        con.execute(
            f"""
            CREATE TEMP VIEW transactions AS
            SELECT *
            FROM read_csv(
                {csv_path_sql},
                header = true,
                all_varchar = true
            )
            """
        )


        result = con.execute(
            """
            SELECT
                COUNT(*) AS total_transactions,
                COUNT(DISTINCT msno) AS unique_customers,
                COUNT(*) - COUNT(msno) AS null_customer_ids,
                ROUND(
                    COUNT(*) * 1.0
                    / NULLIF(COUNT(DISTINCT msno), 0),
                    2
                ) AS avg_transactions_per_customer
            FROM transactions
            """
        ).fetchone()

        if result is None:
            raise RuntimeError(
                "Transaction profiling query returned no results."
            )

        print("\nDATASET SUMMARY")
        print(f"Total transactions: {result[0]:,}")
        print(f"Unique customers: {result[1]:,}")
        print(f"Null customer IDs: {result[2]:,}")
        print(f"Average transactions/customer: {result[3]}")

        
        print("\nDUPLICATE TRANSACTION PROFILING")

        duplicate_result = con.execute(
            """
            WITH duplicate_groups AS (
                SELECT
                    msno,
                    payment_method_id,
                    payment_plan_days,
                    plan_list_price,
                    actual_amount_paid,
                    is_auto_renew,
                    transaction_date,
                    membership_expire_date,
                    is_cancel,
                    COUNT(*) AS occurrence_count
                FROM transactions
                GROUP BY ALL
                HAVING COUNT(*) > 1
            )
            SELECT
                COUNT(*) AS duplicate_groups,
                COALESCE(
                    SUM(occurrence_count - 1), 0
                ) AS extra_duplicate_rows,
                COALESCE(
                    SUM(occurrence_count), 0
                ) AS rows_in_duplicate_groups
            FROM duplicate_groups
            """
        ).fetchone()

        if duplicate_result is None:
            raise RuntimeError(
                "Duplicate profiling returned no results."
            )

        print(
            f"Duplicate groups: {duplicate_result[0]:,}"
        )
        print(
            f"Extra duplicate rows: {duplicate_result[1]:,}"
        )
        print(
            "Rows belonging to duplicate groups: "
            f"{duplicate_result[2]:,}"
        )

        
        print("\nMISSING VALUE PROFILING")

        missing_result = con.execute(
            """
            SELECT
                COUNT(*) AS total_rows,
                COUNT(*) FILTER (
                    WHERE msno IS NULL OR TRIM(msno) = ''
                ) AS missing_msno,
                COUNT(*) FILTER (
                    WHERE payment_method_id IS NULL
                       OR TRIM(payment_method_id) = ''
                ) AS missing_payment_method,
                COUNT(*) FILTER (
                    WHERE payment_plan_days IS NULL
                       OR TRIM(payment_plan_days) = ''
                ) AS missing_plan_days,
                COUNT(*) FILTER (
                    WHERE plan_list_price IS NULL
                       OR TRIM(plan_list_price) = ''
                ) AS missing_list_price,
                COUNT(*) FILTER (
                    WHERE actual_amount_paid IS NULL
                       OR TRIM(actual_amount_paid) = ''
                ) AS missing_amount_paid,
                COUNT(*) FILTER (
                    WHERE is_auto_renew IS NULL
                       OR TRIM(is_auto_renew) = ''
                ) AS missing_auto_renew,
                COUNT(*) FILTER (
                    WHERE transaction_date IS NULL
                       OR TRIM(transaction_date) = ''
                ) AS missing_transaction_date,
                COUNT(*) FILTER (
                    WHERE membership_expire_date IS NULL
                       OR TRIM(membership_expire_date) = ''
                ) AS missing_expire_date,
                COUNT(*) FILTER (
                    WHERE is_cancel IS NULL
                       OR TRIM(is_cancel) = ''
                ) AS missing_cancel
            FROM transactions
            """
        ).fetchone()

        if missing_result is None:
            raise RuntimeError(
                "Missing-value profiling returned no results."
            )

        column_names = [
            "msno",
            "payment_method_id",
            "payment_plan_days",
            "plan_list_price",
            "actual_amount_paid",
            "is_auto_renew",
            "transaction_date",
            "membership_expire_date",
            "is_cancel",
        ]

        total_rows = missing_result[0]

        for column, missing_count in zip(
            column_names,
            missing_result[1:],
            strict=True,
        ):
            missing_pct = (
                100 * missing_count / total_rows
                if total_rows
                else 0
            )

            print(
                f"{column}: {missing_count:,} missing "
                f"({missing_pct:.2f}%)"
            )

        
        print("\nPAYMENT AND PLAN PROFILING")

        payment_result = con.execute(
            """
            WITH typed AS (
                SELECT
                    TRY_CAST(
                        actual_amount_paid AS DOUBLE
                    ) AS amount_paid,
                    TRY_CAST(
                        plan_list_price AS DOUBLE
                    ) AS list_price,
                    TRY_CAST(
                        payment_plan_days AS INTEGER
                    ) AS plan_days
                FROM transactions
            )
            SELECT
                COUNT(*) FILTER (
                    WHERE amount_paid IS NULL
                ) AS invalid_amount_paid,

                COUNT(*) FILTER (
                    WHERE list_price IS NULL
                ) AS invalid_list_price,

                COUNT(*) FILTER (
                    WHERE plan_days IS NULL
                ) AS invalid_plan_days,

                COUNT(*) FILTER (
                    WHERE amount_paid = 0
                ) AS zero_payments,

                COUNT(*) FILTER (
                    WHERE amount_paid < 0
                ) AS negative_payments,

                COUNT(*) FILTER (
                    WHERE amount_paid < list_price
                ) AS below_list_price,

                COUNT(*) FILTER (
                    WHERE amount_paid > list_price
                ) AS above_list_price,

                COUNT(*) FILTER (
                    WHERE plan_days <= 0
                ) AS nonpositive_plan_days,

                MIN(amount_paid) AS min_payment,
                MAX(amount_paid) AS max_payment,
                MIN(plan_days) AS min_plan_days,
                MAX(plan_days) AS max_plan_days
            FROM typed
            """
        ).fetchone()

        if payment_result is None:
            raise RuntimeError(
                "Payment profiling returned no results."
            )

        labels = [
            "Invalid amount paid",
            "Invalid list price",
            "Invalid plan days",
            "Zero payments",
            "Negative payments",
            "Payments below list price",
            "Payments above list price",
            "Nonpositive plan days",
            "Minimum payment",
            "Maximum payment",
            "Minimum plan days",
            "Maximum plan days",
        ]

        for label, value in zip(
            labels,
            payment_result,
            strict=True,
        ):
            print(f"{label}: {value}")

        
        print("\nDATE AND EXPIRY PROFILING")

        date_result = con.execute(
            """
            WITH parsed AS (
                SELECT
                    TRY_STRPTIME(
                        transaction_date, '%Y%m%d'
                    )::DATE AS txn_date,
                    TRY_STRPTIME(
                        membership_expire_date, '%Y%m%d'
                    )::DATE AS expiry_date
                FROM transactions
            )
            SELECT
                COUNT(*) FILTER (
                    WHERE txn_date IS NULL
                ) AS invalid_transaction_dates,

                COUNT(*) FILTER (
                    WHERE expiry_date IS NULL
                ) AS invalid_expiry_dates,

                COUNT(*) FILTER (
                    WHERE expiry_date < txn_date
                ) AS expiry_before_transaction,

                COUNT(*) FILTER (
                    WHERE expiry_date = txn_date
                ) AS expiry_same_day,

                COUNT(*) FILTER (
                    WHERE expiry_date > txn_date
                ) AS expiry_after_transaction,

                MIN(txn_date) AS first_transaction_date,
                MAX(txn_date) AS last_transaction_date,

                MIN(expiry_date) AS earliest_expiry_date,
                MAX(expiry_date) AS latest_expiry_date

            FROM parsed
            """
        ).fetchone()

        if date_result is None:
            raise RuntimeError(
                "Date profiling returned no results."
            )

        labels = [
            "Invalid transaction dates",
            "Invalid expiry dates",
            "Expiry before transaction",
            "Expiry same day",
            "Expiry after transaction",
            "Earliest transaction date",
            "Latest transaction date",
            "Earliest expiry date",
            "Latest expiry date",
        ]

        for label, value in zip(
            labels, date_result, strict=True
        ):
            print(f"{label}: {value}")

        
        print("\nCANCELLATION AND AUTO-RENEWAL PROFILING")

        flag_result = con.execute(
            """
            WITH typed AS (
                SELECT
                    TRY_CAST(is_cancel AS INTEGER)
                        AS cancel_flag,
                    TRY_CAST(is_auto_renew AS INTEGER)
                        AS auto_renew_flag
                FROM transactions
            )
            SELECT
                COUNT(*) AS total_rows,

                COUNT(*) FILTER (
                    WHERE cancel_flag = 0
                ) AS not_cancelled,

                COUNT(*) FILTER (
                    WHERE cancel_flag = 1
                ) AS cancellation_flagged,

                COUNT(*) FILTER (
                    WHERE cancel_flag IS NULL
                       OR cancel_flag NOT IN (0, 1)
                ) AS invalid_cancel_flags,

                COUNT(*) FILTER (
                    WHERE auto_renew_flag = 0
                ) AS auto_renew_off,

                COUNT(*) FILTER (
                    WHERE auto_renew_flag = 1
                ) AS auto_renew_on,

                COUNT(*) FILTER (
                    WHERE auto_renew_flag IS NULL
                       OR auto_renew_flag NOT IN (0, 1)
                ) AS invalid_auto_renew_flags,

                COUNT(*) FILTER (
                    WHERE cancel_flag = 1
                      AND auto_renew_flag = 1
                ) AS cancel_and_auto_renew_on,

                COUNT(*) FILTER (
                    WHERE cancel_flag = 1
                      AND auto_renew_flag = 0
                ) AS cancel_and_auto_renew_off

            FROM typed
            """
        ).fetchone()

        if flag_result is None:
            raise RuntimeError(
                "Cancellation profiling returned no results."
            )

        labels = [
            "Total transactions",
            "Not cancellation-flagged",
            "Cancellation-flagged",
            "Invalid cancellation flags",
            "Auto-renew off",
            "Auto-renew on",
            "Invalid auto-renew flags",
            "Cancellation with auto-renew on",
            "Cancellation with auto-renew off",
        ]

        for label, value in zip(
            labels,
            flag_result,
            strict=True,
        ):
            print(f"{label}: {value:,}")

        print("\nFull-table profiling steps 1-6 completed")


    finally:
        con.close()


if __name__ == "__main__":
    main()
