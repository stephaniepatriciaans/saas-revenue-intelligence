from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "saas_revenue.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        print("\n=== ZERO-PAYMENT PROFILE ===")

        result = con.execute(
            """
            with grouped as (

                select
                    customer_id,
                    transaction_date,
                    count(*) as same_day_count

                from main.stg_transactions

                group by
                    customer_id,
                    transaction_date

            ),

            enriched as (

                select
                    t.*,
                    g.same_day_count

                from main.stg_transactions t

                join grouped g
                    on t.customer_id = g.customer_id
                   and t.transaction_date = g.transaction_date

            )

            select
                count(*) filter (
                    where actual_amount_paid = 0
                ) as zero_payment_rows,

                count(*) filter (
                    where actual_amount_paid = 0
                      and same_day_count > 1
                ) as zero_payment_rows_in_multi_groups,

                count(*) filter (
                    where actual_amount_paid = 0
                      and same_day_count = 1
                ) as zero_payment_rows_in_single_groups,

                count(*) filter (
                    where actual_amount_paid = 0
                      and payment_plan_days > 0
                ) as zero_payment_with_positive_plan_days,

                count(*) filter (
                    where actual_amount_paid = 0
                      and membership_expire_date > transaction_date
                ) as zero_payment_with_future_expiry,

                count(*) filter (
                    where actual_amount_paid = 0
                      and is_auto_renew = 1
                ) as zero_payment_auto_renew_on,

                count(distinct customer_id) filter (
                    where actual_amount_paid = 0
                ) as customers_with_zero_payment

            from enriched
            """
        ).fetchone()

        if result is None:
            raise RuntimeError("Zero-payment profile query returned no result")

        labels = [
            "Zero-payment records",
            "Zero-payment records in multi-transaction days",
            "Zero-payment records in single-transaction days",
            "Zero-payment records with positive plan days",
            "Zero-payment records with future expiry",
            "Zero-payment records with auto-renew on",
            "Customers with zero-payment records",
        ]

        for label, value in zip(labels, result):
            print(f"{label}: {value:,}")

        print("\n=== ZERO-PAYMENT PLAN DURATIONS ===")

        rows = con.execute(
            """
            select
                payment_plan_days,
                count(*) as transaction_count

            from main.stg_transactions

            where actual_amount_paid = 0

            group by payment_plan_days

            order by transaction_count desc

            limit 10
            """
        ).fetchall()

        for days, count in rows:
            print(f"{days} plan days: {count:,} records")

    finally:
        con.close()


if __name__ == "__main__":
    main()
