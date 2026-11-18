-- Every staged transaction must be preserved

with staging_count as (

    select count(*) as row_count
    from {{ ref('stg_transactions') }}

),

intermediate_count as (

    select count(*) as row_count
    from {{ ref('int_transaction_eligibility') }}

)

select
    staging_count.row_count as staging_rows,
    intermediate_count.row_count as intermediate_rows

from staging_count
cross join intermediate_count

where staging_count.row_count <> intermediate_count.row_count
