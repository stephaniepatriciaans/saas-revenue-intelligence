{{ config(materialized='view') }}

with transactions as (

    select *
    from {{ ref('int_transaction_eligibility') }}

),

day_conflicts as (

    select
        customer_id,
        transaction_date,
        transaction_count,
        has_multiple_transactions,
        has_attribute_conflict,
        has_mixed_payment_status

    from {{ ref('int_transaction_day_conflicts') }}

),

coverage_candidates as (

    select
        t.customer_id,
        t.transaction_date,
        t.membership_expire_date,

        t.payment_plan_days,
        t.actual_amount_paid,
        t.plan_list_price,
        t.payment_method_id,
        t.is_auto_renew,
        t.is_cancel,

        t.is_positive_payment,
        t.is_zero_payment,
        t.has_valid_plan_days,
        t.has_valid_date_order,
        t.has_billing_fields,
        t.is_paid_billing_candidate,
        t.has_transaction_anomaly,

        d.transaction_count as same_day_transaction_count,
        d.has_multiple_transactions,
        d.has_attribute_conflict,
        d.has_mixed_payment_status,

        -- Candidate interval: [start_date, end_date)
        -- Expiry treated as exclusive for this candidate model.
        t.transaction_date as candidate_start_date,
        t.membership_expire_date as candidate_end_date,

        (
            t.has_valid_date_order
            and t.has_billing_fields
        ) as has_candidate_coverage,

        (
            t.is_paid_billing_candidate
            and not d.has_attribute_conflict
        ) as is_unambiguous_paid_candidate

    from transactions t

    left join day_conflicts d
        on t.customer_id = d.customer_id
       and t.transaction_date = d.transaction_date

)

select *
from coverage_candidates
