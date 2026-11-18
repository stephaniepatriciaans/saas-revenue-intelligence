from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "saas_revenue.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        print("\n=== 1. TRANSACTION QUALITY ===")

        quality = con.execute(
            """
            select
                count(*) as total_transactions,

                count(*) filter (
                    where actual_amount_paid = 0
                ) as zero_payment_transactions,

                count(*) filter (
                    where payment_plan_days <= 0
                ) as nonpositive_plan_days,

                count(*) filter (
                    where membership_expire_date
                          < transaction_date
                ) as expiry_before_transaction,

                count(*) filter (
                    where membership_expire_date
                          = transaction_date
                ) as expiry_same_day,

                count(*) filter (
                    where is_cancel = 1
                ) as cancellation_flagged

            from main.stg_transactions
            """
        ).fetchone()

        labels = [
            "Total transactions",
            "Zero-payment transactions",
            "Nonpositive plan days",
            "Expiry before transaction",
            "Expiry on transaction day",
            "Cancellation-flagged transactions",
        ]

        if quality is None:
            raise RuntimeError("Transaction quality query returned no result")

        for label, value in zip(labels, quality):
            print(f"{label}: {value:,}")

        print("\n=== 2. SAME-DAY TRANSACTIONS ===")

        same_day = con.execute(
            """
            with daily_transactions as (

                select
                    customer_id,
                    transaction_date,
                    count(*) as transaction_count

                from main.stg_transactions

                group by
                    customer_id,
                    transaction_date
            )

            select
                count(*) filter (
                    where transaction_count > 1
                ) as customer_days_with_multiple_transactions,

                coalesce(
                    sum(transaction_count - 1) filter (
                        where transaction_count > 1
                    ),
                    0
                ) as additional_same_day_transactions,

                coalesce(
                    max(transaction_count),
                    0
                ) as max_transactions_per_customer_day

            from daily_transactions
            """
        ).fetchone()

        if same_day is None:
            raise RuntimeError("Same-day query returned no result")

        print(
            "Customer-days with multiple transactions:",
            f"{same_day[0]:,}",
        )
        print(
            "Additional same-day transactions:",
            f"{same_day[1]:,}",
        )
        print(
            "Maximum transactions in one customer-day:",
            f"{same_day[2]:,}",
        )

        print("\n=== 3. POTENTIAL COVERAGE OVERLAPS ===")

        overlaps = con.execute(
            """
            with daily_coverage as (

                select
                    customer_id,
                    transaction_date,
                    max(membership_expire_date)
                        as max_expiry_date

                from main.stg_transactions

                group by
                    customer_id,
                    transaction_date
            ),

            prior_coverage as (

                select
                    customer_id,
                    transaction_date,
                    max_expiry_date,

                    max(max_expiry_date) over (
                        partition by customer_id
                        order by transaction_date
                        rows between unbounded preceding
                             and 1 preceding
                    ) as prior_max_expiry

                from daily_coverage
            )

            select
                count(*) filter (
                    where prior_max_expiry
                          > transaction_date
                ) as customer_days_before_prior_expiry,

                count(*) filter (
                    where prior_max_expiry
                          = transaction_date
                ) as customer_days_on_prior_expiry,

                count(distinct customer_id) filter (
                    where prior_max_expiry
                          > transaction_date
                ) as customers_with_potential_overlap

            from prior_coverage
            """
        ).fetchone()

        if overlaps is None:
            raise RuntimeError("Overlap query returned no result")

        print(
            "Customer-days before prior expiry:",
            f"{overlaps[0]:,}",
        )
        print(
            "Customer-days on prior expiry:",
            f"{overlaps[1]:,}",
        )
        print(
            "Customers with potential overlap:",
            f"{overlaps[2]:,}",
        )

    finally:
        con.close()


if __name__ == "__main__":
    main()
