import os
import sys
import duckdb
from data_pipeline.extract_load import run_pipeline
from dbt.cli.main import dbtRunner, dbtRunnerResult

def step_1_extract_load() -> None:
    """
    Käivitab andmete laadimise protsessi (E ja L faasid).
    
    See on samm 1/3 kogu andmetöötlusest.
    Käivitatakse 'run_pipeline()' funktsioon, mis tõmbab andmed API-st
    ja salvestab need DuckDB andmebaasi.

    Raises:
        Exception: Kui laadimisprotsess ebaõnnestub (nt API viga),
        prinditakse veateade ja programm peatatakse.
    """
    
    print("\n=== 1. SAMM: Andmete laadimine (DLT) ===")
    
    try:
        # Käivitame andmelaadimise loogika
        run_pipeline()
        
        # Kui vigu ei tekkinud, teavitame edukusest
        print("   -> Andmed edukalt laetud faili 'tai_data.duckdb'")
        
    except Exception as e:
        # Püüame kinni kõik võimalikud vead (nt võrguühendus, failiõigused)
        print(f"\n   -> VIGA andmete laadimisel: {e}")
        print("      Kontrolli internetiühendust ja API URL-i.")
        
        # Peatame programmi täitmise veakoodiga 1 (FAILURE)
        sys.exit(1)

def step_2_transform() -> None:
    """
    Käivitab dbt (Data Build Tool) transformatsioonid (T faas).
    
    See on samm 2/3 andmetöötlusprotsessist.
    Käsk 'dbt build' teeb kolme asja korraga:
    1. Loob tabelid ja vaated (views) andmebaasis ('analytics' skeemis).
    2. Testib andmete kvaliteeti (dbt tests).
    3. Täidab mudelid andmetega (seeds).

    NB! See samm eeldab, et 'tai_data.duckdb' fail on juba olemas
    ja sisaldab andmeid (Step 1 õnnestus).
    """

    print("\n=== 2. SAMM: Transformatsioonid (DBT) ===")
    
    # 1. Konfiguratsioon
    # Kus asub dbt projektikaust (mis sisaldab dbt_project.yml faili)?
    PROJECT_DIR = "dbt_project"
    
    # Kus asub profiles.yml fail (ühenduse seadistused)?
    # Tavaliselt on see ~/.dbt/, aga meie projektis on see projekti sees.
    PROFILES_DIR = "dbt_project"

    # 2. Initsialiseeri dbtRunner
    dbt = dbtRunner()
    
    # 3. Käivitusargumendid (CLI arguments)
    # Kasutame käsku 'build', mis on turvalisem ja täielikum kui 'run'.
    # See jooksutab mudelid ja testid koos.
    cli_args = [
        "build", 
        "--project-dir", PROJECT_DIR, 
        "--profiles-dir", PROFILES_DIR
    ]
    
    # 4. Käivita dbt ja püüa tulemus
    # invoke() käivitab dbt samamoodi nagu käsurealt 'dbt build ...'
    res: dbtRunnerResult = dbt.invoke(cli_args)
    
    # 5. Kontrolli tulemust (Error Handling)
    if not res.success:
        print("   -> VIGA: dbt mudelite ehitamine ebaõnnestus!")
        
        # Kui dbt viskas konkreetse Pythoni erandi, viska see edasi
        if res.exception:
            raise res.exception
            
        # Kui erandit polnud, aga käsk ebaõnnestus (nt SQL süntaksiviga),
        # lõpeta programm veakoodiga 1.
        sys.exit(1)

    print(f"   -> Mudelid edukalt loodud ja testitud (schema 'analytics')")

def step_3_export_parquet() -> None:
    """
    Ekspordib dbt poolt loodud analüütilised tabelid Parquet failideks.
    
    See on samm 3/3.
    Parquet failid on optimeeritud lugemiseks Power BI-s.
    Iga tabel salvestatakse eraldi failina kausta 'visualiseering/'.

    Raises:
        duckdb.CatalogException: Kui tabelit ei leita andmebaasist (nt dbt viga).
        OSError: Kui faili kirjutamisel tekib viga (nt õigused).
    """

    print("\n=== 3. SAMM: Eksport Parquet faili (Power BI jaoks) ===")

    # 1. Konfiguratsioon
    OUTPUT_DIR = "visualiseering"
    DB_PATH = "tai_data.duckdb"
    SCHEMA = "analytics" # Peab klappima dbt profiles.yml failiga!

    # Tabelid, mida soovime eksportida (peavad olemas olema dbt mudelitena)
    TABLES_TO_EXPORT = [
        "fct_providers",
        "dim_location",
        "dim_owner",
        "dim_size",
        "dim_year" 
    ]

    # 2. Loo väljundkaust, kui seda pole
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"   Loodi kaust: {OUTPUT_DIR}")
        except OSError as e:
            print(f"   VIGA: Ei saanud kausta luua: {e}")
            return # Lõpeta funktsioon, sest edasi minna pole mõtet

    # 3. Ühendu andmebaasiga ja ekspordi
    # 'with' statement tagab ühenduse automaatse sulgemise
    try:
        with duckdb.connect(DB_PATH) as con:
            
            exported_count = 0
            
            for table in TABLES_TO_EXPORT:
                output_file = os.path.join(OUTPUT_DIR, f"{table}.parquet")
                
                print(f"   ... Ekspordin: {table} -> {output_file}")
                
                # Kustuta vana fail, et vältida kirjutamisvigu
                if os.path.exists(output_file):
                    os.remove(output_file)
                
                # DuckDB SQL käsk eksportimiseks
                # Kasutame f-stringi tabeli nime sisestamiseks
                query = f"COPY (SELECT * FROM {SCHEMA}.{table}) TO '{output_file}' (FORMAT PARQUET)"
                
                con.sql(query)
                exported_count += 1
            
            print(f"\n   -> KÕIK VALMIS! {exported_count} faili salvestatud kausta '{OUTPUT_DIR}/'")

    except duckdb.CatalogException as e:
        print(f"\n   -> VIGA: Tabelit ei leitud andmebaasist!")
        print(f"      Kontrolli, kas dbt mudel '{table}' (failinimi) on õige.")
        print(f"      Tehniline viga: {e}")
        
    except Exception as e:
        print(f"\n   -> VIGA eksportimisel: {e}")

if __name__ == "__main__":
    step_1_extract_load()
    step_2_transform()
    step_3_export_parquet()
    print("\n=== VALMIS! Ava nüüd Power BI ja lae failid 'visualiseering/*.parquet' ===")