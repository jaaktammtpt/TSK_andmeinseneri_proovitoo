with stg as (
    select * from {{ ref('stg_providers') }}
)

select
    -- Foreign Keys (Dimensioonide võtmed)
    md5(asukoht_nimi) as location_id,
    md5(omaniku_liik) as owner_id,
    md5(suurus_kategooria) as size_id,
    
    aasta as year_id, -- Viitab dim_year.year_id veerule
    
    -- Measures (Mõõdikud)
    asutuste_arv
from stg