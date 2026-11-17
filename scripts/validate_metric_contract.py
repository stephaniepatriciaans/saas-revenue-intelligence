"""Validate Phase 1 SaaS financial metric contracts
All test values are synthetic
"""

from math import isclose


def normalized_mrr(amount_paid, plan_days):
    """Normalize a day-based subscription to average monthly value"""
    if amount_paid < 0:
        raise ValueError("Amount cannot be negative")
    if plan_days <= 0:
        raise ValueError("Plan duration must be positive")

    return amount_paid * 365.25 / (12 * plan_days)


def calculate_arr(mrr):
    """Calculate annualized recurring revenue run-rate"""
    if mrr < 0:
        raise ValueError("MRR cannot be negative")
    return mrr * 12


def calculate_nrr(start, expansion, contraction, churn):
    """Calculate NRR for the opening customer cohort"""
    if start <= 0:
        raise ValueError("Starting MRR must be positive")

    return (start + expansion - contraction - churn) / start


def calculate_churn(churned_customers, starting_customers):
    """Calculate opening-cohort customer churn"""
    if starting_customers <= 0:
        raise ValueError("Starting customers must be positive")
    if not 0 <= churned_customers <= starting_customers:
        raise ValueError("Invalid churned customer count")

    return churned_customers / starting_customers


def calculate_gross_margin(revenue, cost_rate):
    """Scenario-based gross margin, not observed profitability"""
    if revenue <= 0:
        raise ValueError("Revenue must be positive")
    if not 0 <= cost_rate <= 1:
        raise ValueError("Invalid assumed cost rate")

    return 1 - cost_rate


def test_metrics():
    # Synthetic financial examples in TWD

    assert isclose(normalized_mrr(27, 90), 9.13125)
    assert calculate_arr(10000) == 120000

    assert isclose(
        calculate_nrr(100000, 8000, 3000, 7000),
        0.98,
    )

    assert isclose(calculate_churn(20, 200), 0.10)
    assert isclose(calculate_gross_margin(100000, 0.30), 0.70)

    # Synthetic monthly MRR reconciliation
    starting_mrr = 100000
    new_mrr = 10000
    reactivation_mrr = 2000
    expansion_mrr = 5000
    contraction_mrr = 3000
    churned_mrr = 4000

    ending_mrr = (
        starting_mrr
        + new_mrr
        + reactivation_mrr
        + expansion_mrr
        - contraction_mrr
        - churned_mrr
    )

    assert ending_mrr == 110000

    # Validate input guardrails
    try:
        normalized_mrr(100, 0)
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass

    print("All Phase 1 metric validation checks passed!")


if __name__ == "__main__":
    test_metrics()
