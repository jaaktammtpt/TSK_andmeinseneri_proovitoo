select distinct
    -- Genererime unikaalse ID
    md5(asukoht_nimi) as location_id,
    asukoht_nimi as linn_või_vald,
    maakond_grupp as maakond
from {{ ref('stg_providers') }}