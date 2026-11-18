from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "saas_revenue.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        print("\n=== ZERO-PAYMENT CUSTOMER HISTORY ===")

        result = con.execute(
            """
            with customer_history as (

                select
                    customer_id,

                    count(*) filter (
                        where actual_amount_paid = 0
                    ) as zero_payment_count,

                    count(*) filter (
                        where actual_amount_paid > 0
                    ) as paid_transaction_count

                from main.stg_transactions

                group by customer_id

            )

            select
                count(*) filter (
                    where zero_payment_count > 0
                ) as customers_with_zero_payments,

                count(*) filter (
                    where zero_payment_count > 0
                      and paid_transaction_count > 0
                ) as customers_with_both,

                count(*) filter (
                    where zero_payment_count > 0
                      and paid_transaction_count = 0
                ) as customers_with_only_zero_payments

            from customer_history
            """
        ).fetchone()

        if result is None:
            raise RuntimeError("Customer history query returned no result")

        labels = [
            "Customers with zero-payment records",
            "Customers with both zero and positive payments",
            "Customers with only zero-payment records",
        ]

        for label, value in zip(labels, result):
            print(f"{label}: {value:,}")

        print("\n=== ZERO-PAYMENT EVENT TIMING ===")

        timing = con.execute(
            """
            with zero_events as (

                select
                    customer_id,
                    transaction_date

                from main.stg_transactions

                where actual_amount_paid = 0

            ),

            classified as (

                select
                    z.customer_id,
                    z.transaction_date,

                    exists (
                        select 1
                        from main.stg_transactions p
                        where p.customer_id = z.customer_id
                          and p.actual_amount_paid > 0
                          and p.transaction_date
                              < z.transaction_date
                    ) as has_earlier_paid_transaction,

                    exists (
                        select 1
                        from main.stg_transactions p
                        where p.customer_id = z.customer_id
                          and p.actual_amount_paid > 0
                          and p.transaction_date
                              <= z.transaction_date
                          and p.membership_expire_date
                              > z.transaction_date
                    ) as has_paid_record_covering_date

                from zero_events z

            )

            select
                count(*) as zero_payment_events,

                count(*) filter (
                    where has_earlier_paid_transaction
                ) as events_with_earlier_paid_history,

                count(*) filter (
                    where has_paid_record_covering_date
                ) as events_with_paid_record_covering_date,

                count(*) filter (
                    where not has_earlier_paid_transaction
                ) as events_without_earlier_paid_history

            from classified
            """
        ).fetchone()

        if timing is None:
            raise RuntimeError("Event timing query returned no result")

        labels = [
            "Zero-payment events",
            "Events with earlier positive-payment history",
            "Events with paid record covering event date",
            "Events without earlier positive-payment history",
        ]

        for label, value in zip(labels, timing):
            print(f"{label}: {value:,}")

    finally:
        con.close()


if __name__ == "__main__":
    main()
