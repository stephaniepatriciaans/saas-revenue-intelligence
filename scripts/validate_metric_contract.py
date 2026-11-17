from math import isclose


def normalized_mrr(amount, days):
    if amount < 0 or days <= 0:
        raise ValueError("Invalid subscription inputs")
    return amount * 365.25 / (12 * days)


def nrr(starting, expansion, contraction, churn):
    if starting <= 0:
        raise ValueError("Starting MRR must be positive")
    return (
        starting + expansion - contraction - churn
    ) / starting


def gross_margin(revenue, cost_rate):
    if revenue <= 0:
        raise ValueError("Revenue must be positive")
    if not 0 <= cost_rate <= 1:
        raise ValueError("Invalid cost rate")
    return 1 - cost_rate


def test_metric_examples():
    # All values below are synthetic examples.
    assert isclose(normalized_mrr(27, 90), 9.13125)

    assert isclose(
        nrr(100000, 8000, 3000, 7000),
        0.98
    )

    assert isclose(
        gross_margin(100000, 0.30),
        0.70
    )

    starting = 100000
    new = 5000
    reactivated = 2000
    expansion = 8000
    contraction = 3000
    churned = 7000

    ending = (
        starting + new + reactivated
        + expansion - contraction - churned
    )

    assert ending == 105000


if __name__ == "__main__":
    test_metric_examples()
    print("All metric contract checks passed.")
