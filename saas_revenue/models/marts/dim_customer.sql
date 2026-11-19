{{ config(materialized='view') }}
-- Includes all source members, not just customers with transactions.
select
    customer_id, city_code, age_raw, gender,
    registration_method_id, registration_date
from {{ ref('stg_members') }}
