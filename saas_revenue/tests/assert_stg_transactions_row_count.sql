-- Return a row only when raw and staging counts differ.
-- A dbt singular test passes when this query returns zero rows.

with raw_count as (

    select count(*) as row_count
    from {{ source('kkbox', 'transactions_v2') }}

),

staging_count as (

    select count(*) as row_count
    from {{ ref('stg_transactions') }}

)

select
    raw_count.row_count as raw_rows,
    staging_count.row_count as staging_rows

from raw_count
cross join staging_count

where raw_count.row_count <> staging_count.row_count
