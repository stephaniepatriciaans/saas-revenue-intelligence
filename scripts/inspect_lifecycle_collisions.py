from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "saas_revenue.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        print("\n=== TOP 10 SAME-DAY TRANSACTION GROUPS ===")

        results = con.execute(
            """
            select
                transaction_date,
                count(*) as transactions,
                count(distinct membership_expire_date)
                    as distinct_expiry_dates,
                count(distinct payment_plan_days)
                    as distinct_plan_durations,
                count(distinct actual_amount_paid)
                    as distinct_payment_amounts,
                count(*) filter (
                    where actual_amount_paid = 0
                ) as zero_payment_rows,
                count(*) filter (
                    where is_cancel = 1
                ) as cancellation_rows,
                sum(actual_amount_paid)
                    as total_recorded_payments

            from main.stg_transactions

            group by
                customer_id,
                transaction_date

            having count(*) > 1

            order by
                transactions desc,
                transaction_date

            limit 10
            """
        ).fetchall()

        print(
            "date | transactions | expiry_values | "
            "plan_values | payment_values | "
            "zero_payments | cancellations | payment_sum"
        )

        for row in results:
            print(" | ".join(str(value) for value in row))

        print("\n=== SAME-DAY GROUP SIZE DISTRIBUTION ===")

        distribution = con.execute(
            """
            with grouped as (

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
                case
                    when transaction_count = 1 then '1'
                    when transaction_count = 2 then '2'
                    when transaction_count between 3 and 5
                        then '3-5'
                    when transaction_count between 6 and 10
                        then '6-10'
                    when transaction_count between 11 and 50
                        then '11-50'
                    else '51+'
                end as size_bucket,

                count(*) as customer_days

            from grouped

            group by 1

            order by
                case size_bucket
                    when '1' then 1
                    when '2' then 2
                    when '3-5' then 3
                    when '6-10' then 4
                    when '11-50' then 5
                    else 6
                end
            """
        ).fetchall()

        for bucket, count in distribution:
            print(f"{bucket} transactions: {count:,} customer-days")

    finally:
        con.close()


if __name__ == "__main__":
    main()
