import dlt
import requests
import pandas as pd
from pyjstat import pyjstat


def get_tai_data() -> pd.DataFrame:
    """
    Pärib TAI statistika andmebaasist tervishoiuteenuse osutajate andmed (TTO15).
    
    Päring tehakse JSON-stat formaadis ja konverteeritakse Pandas DataFrame'iks.
    Tühi "query" list tähendab, et API-st küsitakse kõik saadaolevad andmed 
    ilma filtriteta.

    Returns:
        pd.DataFrame: Töötlemata andmed (raw data) tabelina.
    Raises:
        requests.exceptions.HTTPError: Kui API päring ebaõnnestub (nt 404 või 500).
    """
    
    # API otspunkt (Endpoint) TAI andmebaasis
    url = "https://statistika.tai.ee/api/v1/et/Andmebaas/04THressursid/01TTosutajad/TTO15.px"

    # Päringu keha (Payload). 
    # Määrame soovitud vastuse formaadi (json-stat).
    query = {
        "query": [],
        "response": {
            "format": "json-stat"
        }
    }

    # Teeme POST päringu API-sse
    response = requests.post(url, json=query)

    # Kontrollime, kas päring õnnestus.
    # Kui staatuskood on 4xx või 5xx, viskab see rida veateate ja peatab skripti.
    response.raise_for_status()

    # Töötleme vastuse:
    # 1. Loeme JSON-stat teksti pyjstat objekti sisse
    dataset = pyjstat.Dataset.read(response.text)
    
    # 2. Kirjutame andmed Pandas DataFrame formaati
    df = dataset.write('dataframe')

    print(f"Laeti {len(df)} rida andmeid.")
    
    return df

def run_pipeline() -> None:
    """
    Käivitab täieliku andmete laadimise protsessi (ETL).

    See funktsioon:
    1. Defineerib dlt pipeline'i seadistuse.
    2. Laeb andmed DuckDB andmebaasi tabelisse 'tt_osutajad'.
    3. Asendab ('replace') vanad andmed uutega.

    """
    # 1. Pipeline'i seadistused (Konstandid)
    PIPELINE_NAME = "tai_pipeline"
    DB_FILE = "tai_data.duckdb"
    SCHEMA = "raw_data"
    TABLE_NAME = "tt_osutajad"

    # 2. Initsialiseerime dlt pipeline'i.
    # See loob ühenduse DuckDB-ga ja valmistab ette skeemi.
    pipeline = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination=dlt.destinations.duckdb(DB_FILE),
        dataset_name=SCHEMA,
        # Logimise seadistus (valikuline, kuid hea praktika)
        progress="log"
    )

    # 3. Päri andmed (Eelnevalt defineeritud funktsioon)
    print("Laeme andmeid TAI API-st...")
    data = get_tai_data()

    # 4. Käivita laadimine (Load)
    # write_disposition="replace" kustutab vana tabeli sisu ja kirjutab uue asemele.
    # See sobib hästi väiksemate andmekogumite (Full Load) puhul.
    info = pipeline.run(
        data, 
        table_name=TABLE_NAME, 
        write_disposition="replace"
    )

    # 5. Prindi kokkuvõte laadimisest
    print(info)

if __name__ == "__main__":
    run_pipeline()