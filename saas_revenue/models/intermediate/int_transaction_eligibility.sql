{{ config(materialized='view') }}

with source as (

    select *
    from {{ ref('stg_transactions') }}

),

classified as (

    select
        *,

        -- Payment classifications
        (actual_amount_paid > 0)
            as is_positive_payment,

        (actual_amount_paid = 0)
            as is_zero_payment,

        -- Plan duration classification
        (payment_plan_days > 0)
            as has_valid_plan_days,

        -- Date-order classification
        (membership_expire_date > transaction_date)
            as has_valid_date_order,

        -- Completeness of required billing fields
        (
            customer_id is not null
            and actual_amount_paid is not null
            and payment_plan_days is not null
            and transaction_date is not null
            and membership_expire_date is not null
        ) as has_billing_fields

    from source

),

eligibility as (

    select
        *,

        (
            has_billing_fields
            and is_positive_payment
            and has_valid_plan_days
            and has_valid_date_order
        ) as is_paid_billing_candidate,

        (
            not has_billing_fields
            or actual_amount_paid < 0
            or payment_plan_days <= 0
            or membership_expire_date
               <= transaction_date
        ) as has_transaction_anomaly

    from classified

)

select *
from eligibility
