{{ config(materialized='view') }}

with source as (

    select *
    from {{ source('kkbox', 'members_v3') }}

),

typed as (

    select
        trim(msno) as customer_id,

        try_cast(city as integer)
            as city_code,

        try_cast(bd as integer)
            as age_raw,

        nullif(trim(gender), '')
            as gender,

        try_cast(registered_via as integer)
            as registration_method_id,

        try_strptime(
            registration_init_time, '%Y%m%d'
        )::date as registration_date,

        _source_file,
        _ingested_at

    from source

)

select *
from typed
