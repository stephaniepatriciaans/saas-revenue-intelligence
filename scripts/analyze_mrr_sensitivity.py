"""Compare modeled MRR under alternative expiry-duration thresholds"""

import csv
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "saas_revenue.duckdb"
OUTPUT_PATH = ROOT / "data" / "processed" / "mrr_sensitivity.csv"

THRESHOLDS = [90, 180, 365, 450, 730]
BASELINE = 450

con = duckdb.connect(str(DB_PATH), read_only=True)

results = []

for days in THRESHOLDS:
    print(f"Analyzing {days}-day threshold...", flush=True)

    # Recompute both guardrail flags under the scenario.
    # No source transaction or dbt model is changed.
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW scenario_candidates AS
        SELECT
            *,
            (
                has_candidate_coverage
                AND NOT COALESCE(recorded_coverage_days > {days}, FALSE)
                AND NOT COALESCE(payment_plan_days > {days}, FALSE)
                AND NOT COALESCE(
                    outside_observed_transaction_window, FALSE
                )
            ) AS scenario_coverage,

            (
                is_paid_billing_candidate
                AND NOT COALESCE(has_attribute_conflict, FALSE)
                AND NOT COALESCE(recorded_coverage_days > {days}, FALSE)
                AND NOT COALESCE(payment_plan_days > {days}, FALSE)
                AND NOT COALESCE(
                    outside_observed_transaction_window, FALSE
                )
            ) AS scenario_paid

        FROM main.int_coverage_guardrails
    """)

    query = """
        WITH active AS (
            SELECT
                cm.customer_id,
                cm.month_end,

                COUNT(t.customer_id) AS active_candidates,

                COUNT(t.customer_id) FILTER (
                    WHERE t.scenario_paid
                ) AS eligible_paid,

                COUNT(t.customer_id) FILTER (
                    WHERE NOT t.scenario_coverage
                       OR (
                           t.is_positive_payment
                           AND NOT t.scenario_paid
                       )
                ) AS unresolved,

                MAX(
                    CASE
                        WHEN t.scenario_paid
                        THEN t.actual_amount_paid * 365.25
                            / (
                                12.0 *
                                NULLIF(t.payment_plan_days, 0)
                            )
                    END
                ) AS normalized_mrr

            FROM main.fct_customer_month cm

            LEFT JOIN scenario_candidates t
                ON cm.customer_id = t.customer_id
               AND t.candidate_start_date <= cm.month_end
               AND t.candidate_end_date > cm.month_end

            GROUP BY cm.customer_id, cm.month_end
        ),

        classified AS (
            SELECT
                month_end,

                CASE
                    WHEN unresolved > 0 OR eligible_paid > 1
                        THEN 'ambiguous'
                    WHEN eligible_paid = 1
                        THEN 'estimated_paid_active'
                    WHEN active_candidates > 0
                        THEN 'other_coverage_only'
                    ELSE 'no_observed_coverage'
                END AS state,

                CASE
                    WHEN unresolved = 0 AND eligible_paid = 1
                    THEN CAST(normalized_mrr AS DECIMAL(18, 2))
                END AS estimated_mrr

            FROM active
        )

        SELECT
            month_end,
            COUNT(*) FILTER (
                WHERE state = 'estimated_paid_active'
            ) AS estimated_paid_customers,

            COUNT(*) FILTER (
                WHERE state = 'ambiguous'
            ) AS ambiguous_customer_months,

            COALESCE(SUM(estimated_mrr), 0)
                AS estimated_mrr_twd

        FROM classified
        GROUP BY month_end
        ORDER BY month_end
    """

    cursor = con.execute(query)
    for month_end, paid, ambiguous, mrr in cursor.fetchall():
        results.append({
            "threshold_days": days,
            "month_end": str(month_end),
            "estimated_paid_customers": paid,
            "ambiguous_customer_months": ambiguous,
            "estimated_mrr_twd": mrr,
            "estimated_arr_twd": mrr * 12,
        })

# Important: The 450-day scenario should reproduce the
# committed baseline model exactly, including customer-month
# rounding and ambiguity treatment
baseline_rows = {
    str(month_end): (paid, ambiguous, mrr)
    for month_end, paid, ambiguous, mrr in con.execute("""
        SELECT
            month_end,
            estimated_paid_customers,
            ambiguous_customer_months,
            included_estimated_mrr_twd
        FROM main.mart_monthly_kpis
    """).fetchall()
}

scenario_450 = [
    row for row in results
    if row["threshold_days"] == BASELINE
]

assert len(scenario_450) == len(baseline_rows), (
    "Baseline month count does not reconcile"
)

for row in scenario_450:
    expected = baseline_rows[row["month_end"]]
    actual = (
        row["estimated_paid_customers"],
        row["ambiguous_customer_months"],
        row["estimated_mrr_twd"],
    )
    assert actual == expected, (
        f"Baseline reconciliation failed: {row['month_end']}\n"
        f"Expected: {expected}\nActual: {actual}"
    )

print("\n450-day baseline reconciles with dbt mart.")

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_PATH.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "threshold_days",
        "month_end",
        "estimated_paid_customers",
        "ambiguous_customer_months",
        "estimated_mrr_twd",
        "estimated_arr_twd",
    ])
    writer.writeheader()
    writer.writerows(results)

print(f"\nSaved: {OUTPUT_PATH}")

print("\n=== MARCH 2017 SENSITIVITY ===")
for row in results:
    if row["month_end"] == "2017-03-31":
        print(
            f"{row['threshold_days']:>3} days | "
            f"Paid: {row['estimated_paid_customers']:>9,} | "
            f"Ambiguous: {row['ambiguous_customer_months']:>9,} | "
            f"MRR: NT${row['estimated_mrr_twd']:>15,.2f}"
        )

con.close()
