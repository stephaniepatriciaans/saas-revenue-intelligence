{{ config(materialized='view') }}

with source as (

    select *
    from {{ source('kkbox', 'transactions_v2') }}

),

typed as (

    select
        trim(msno) as customer_id,

        try_cast(payment_method_id as integer)
            as payment_method_id,

        try_cast(payment_plan_days as integer)
            as payment_plan_days,

        try_cast(plan_list_price as decimal(18, 2))
            as plan_list_price,

        try_cast(actual_amount_paid as decimal(18, 2))
            as actual_amount_paid,

        try_cast(is_auto_renew as integer)
            as is_auto_renew,

        try_strptime(transaction_date, '%Y%m%d')::date
            as transaction_date,

        try_strptime(membership_expire_date, '%Y%m%d')::date
            as membership_expire_date,

        try_cast(is_cancel as integer)
            as is_cancel,

        _source_file,
        _ingested_at

    from source

)

select *
from typed
