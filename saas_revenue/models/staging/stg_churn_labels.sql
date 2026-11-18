{{ config(materialized='view') }}

with source as (

    select *
    from {{ source('kkbox', 'train_v2') }}

),

typed as (

    select
        trim(msno) as customer_id,

        try_cast(is_churn as integer)
            as is_churn,

        _source_file,
        _ingested_at

    from source

)

select *
from typed
