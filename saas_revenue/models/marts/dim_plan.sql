{{ config(materialized='view') }}
-- This is a source attribute combination, NOT an official KKBox product/plan ID.
select distinct
    md5(concat_ws('|', cast(payment_method_id as varchar),
        cast(payment_plan_days as varchar), cast(plan_list_price as varchar)))
        as plan_attribute_key,
    payment_method_id,
    payment_plan_days,
    plan_list_price
from {{ ref('stg_transactions') }}
