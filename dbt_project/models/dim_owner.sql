select distinct
    md5(omaniku_liik) as owner_id,
    omaniku_liik
from {{ ref('stg_providers') }}