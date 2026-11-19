{{ config(materialized='view') }}
-- Source transaction row grain. No invented event ID.
select * from {{ ref('int_transaction_eligibility') }}
