import duckdb
    
con = duckdb.connect('tai_data.duckdb')
print("\n=== TABELID ANDMEBAASIS ===")
con.sql("SHOW ALL TABLES").show()
    
print("\n=== NÄIDIS: Fct_Providers ===")
try:
    con.sql("SELECT * FROM analytics.fct_providers LIMIT 5").show()
except:
        print("Tabelit ei leitud (kas dbt on jooksutatud?)")