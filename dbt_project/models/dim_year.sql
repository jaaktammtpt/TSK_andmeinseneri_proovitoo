with distinct_years as (
    select distinct 
        aasta 
    from {{ ref('stg_providers') }}
)

select
    aasta as year_id, -- See on meie võti (Primary Key)
    aasta,
    cast(aasta as VARCHAR) || '. a' as aasta_nimi
    
from distinct_years
order by aasta desc