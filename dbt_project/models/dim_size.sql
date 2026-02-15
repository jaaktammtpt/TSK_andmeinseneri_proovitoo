select distinct
    md5(suurus_kategooria) as size_id,
    suurus_kategooria,
    -- Lisame sortimise loogika
    CASE 
        WHEN suurus_kategooria LIKE '1-2%' THEN 1
        WHEN suurus_kategooria LIKE '3-9%' THEN 2
        WHEN suurus_kategooria LIKE '10-19%' THEN 3
        WHEN suurus_kategooria LIKE '20-49%' THEN 4
        WHEN suurus_kategooria LIKE '50-99%' THEN 5
        WHEN suurus_kategooria LIKE '100-249%' THEN 6
        WHEN suurus_kategooria LIKE '250%' THEN 7
        ELSE 99
    END as sort_order
from {{ ref('stg_providers') }}