select *
from {{ ref('fct_providers') }}
where asutuste_arv <= 0