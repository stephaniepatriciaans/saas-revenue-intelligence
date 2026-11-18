-- Fails when transaction classifications contradict
-- the documented eligibility and anomaly rules

select
    customer_id,
    transaction_date,
    actual_amount_paid,
    payment_plan_days,
    membership_expire_date

from {{ ref('int_transaction_eligibility') }}

where
    is_paid_billing_candidate is distinct from (
        has_billing_fields
        and actual_amount_paid > 0
        and payment_plan_days > 0
        and membership_expire_date > transaction_date
    )

    or has_transaction_anomaly is distinct from (
        not has_billing_fields
        or actual_amount_paid < 0
        or payment_plan_days <= 0
        or membership_expire_date <= transaction_date
    )
