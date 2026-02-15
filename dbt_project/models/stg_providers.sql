/*
    Mudel: stg_providers.sql
    Eesmärk: Puhastab ja normaliseerib tervishoiuteenuse osutajate andmed.
    
    Peamine äriloogika (Business Logic):
    TAI algandmetes sisaldab maakonna rida (nt "Harju maakond") ka linna (nt "Tallinn") summat.
    Power BI-s korrektseks summeerimiseks peame tekitama üksteist välistavad kategooriad:
      1. Tallinn (eraldi)
      2. Harju maakond (ilma Tallinnata)
    
    See väldib topeltarvestust (Double Counting), kui kasutaja valib filtrist terve maakonna.
*/

with source as (
    select * from {{ source('tai_raw', 'tt_osutajad') }}
),

cleaned_data as (
    -- 1. Esmalt puhastame andmetüübid ja filtreerime välja müra
    select
        "aasta" as aasta,
        "omaniku_liik" as omaniku_liik,
        "tervishoiut_tajate_arv" as suurus_kategooria,
        
        -- Eemaldame hierarhia tähised (..) nimede eest
        REPLACE("maakond", '..', '') as asukoht_nimi,
        
        -- Teisendame teksti numbriks ja asendame NULL-id nulliga arvutuste lihtsustamiseks
        COALESCE(TRY_CAST("value" as INTEGER), 0) as asutuste_arv
    from source
    where 
        -- Eemaldame algandmetest summaarsed read, et vältida duplikaate
        "maakond" != 'Eesti'
        AND "omaniku_liik" != 'Avalik ja erasektor kokku'
        AND "tervishoiut_tajate_arv" != 'Tervishoiuteenuse osutajad kokku'
),

cities as (
    -- 2. Eraldame linnad (Tallinn ja Tartu) ajutisse tabelisse.
    -- Neid andmeid kasutame hiljem maakonna kogusummast lahutamiseks.
    select * 
    from cleaned_data 
    where asukoht_nimi in ('Tallinn', 'Tartu')
),

calculated_logic as (
    -- 3. Rakendame "Maakond miinus Linn" loogika
    select
        main.aasta,
        main.omaniku_liik,
        main.suurus_kategooria,
        
        -- Nimetame maakonnad ümber, et kasutajale oleks selge, mida rida sisaldab
        CASE 
            WHEN main.asukoht_nimi = 'Harju maakond' THEN 'Harju maakond (v.a. Tallinn)'
            WHEN main.asukoht_nimi = 'Tartu maakond' THEN 'Tartu maakond (v.a. Tartu linn)'
            ELSE main.asukoht_nimi 
        END as asukoht_nimi,
        
        -- Loome hierarhia veeru Power BI "Drill-down" funktsionaalsuse jaoks.
        -- Nt: Harju Maakond -> [Tallinn, Harju vald, ...]
        CASE 
            WHEN main.asukoht_nimi = 'Harju maakond' OR main.asukoht_nimi = 'Tallinn' THEN 'Harju maakond'
            WHEN main.asukoht_nimi = 'Tartu maakond' OR main.asukoht_nimi = 'Tartu' THEN 'Tartu maakond'
            ELSE main.asukoht_nimi 
        END as maakond_grupp,

        -- ARVUTUS: Lahutame linna väärtuse maakonna summast.
        -- Valem: Puhas Maakond = Maakond (koos linnaga) - Linn
        CASE 
            WHEN main.asukoht_nimi = 'Harju maakond' THEN 
                main.asutuste_arv - COALESCE(tallinn.asutuste_arv, 0)
            
            WHEN main.asukoht_nimi = 'Tartu maakond' THEN 
                main.asutuste_arv - COALESCE(tartu.asutuste_arv, 0)
            
            ELSE main.asutuste_arv
        END as asutuste_arv

    from cleaned_data main
    
    -- Ühendame (Join) Tallinna andmed Harju ridade külge, et teha arvutus samal real
    left join cities tallinn 
        on main.aasta = tallinn.aasta 
        and main.omaniku_liik = tallinn.omaniku_liik 
        and main.suurus_kategooria = tallinn.suurus_kategooria
        and tallinn.asukoht_nimi = 'Tallinn'
        
    -- Ühendame Tartu andmed Tartu maakonna ridade külge
    left join cities tartu 
        on main.aasta = tartu.aasta 
        and main.omaniku_liik = tartu.omaniku_liik 
        and main.suurus_kategooria = tartu.suurus_kategooria
        and tartu.asukoht_nimi = 'Tartu'
)

select * 
from calculated_logic
where asutuste_arv > 0 -- Eemaldame tühjad read (nt kui maakonnas on asutusi 0 pärast lahutamist)