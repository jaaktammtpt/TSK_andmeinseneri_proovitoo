# Tervishoiuteenuse osutajate andmete ETL

See projekt on koostatud kandideerimiseks **Tallinna Strateegiakeskuse andmeinseneri** ametikohale.

Projekti eesmärk on luua automaatne andmetoru (ETL pipeline), mis laeb TAI andmebaasist alla tervishoiuteenuse osutajate statistika, puhastab andmed, loob analüütilise andmemudeli ja salvestab tulemused Power BI jaoks sobivasse formaati.

## 🛠 Kasutatud tehnoloogiad ja valikute põhjendused

Lahenduses on kasutatud kaasaegset andmeplatvormi (*Modern Data Stack*) lähenemist, kuid hoitud see lihtsasti käivitatavana (ilma Dockerita).

*   **Python + dlt (Data Load Tool):** Kasutatud andmete laadimiseks (Extract & Load). `dlt` tegeleb automaatselt API päringute, skeemi tuvastamise ja normaliseerimisega. See on töökindlam kui lihtsad *requests* skriptid.
*   **DuckDB:** Valitud andmebaasiks, kuna see on serverivaba (*in-process* OLAP andmebaas). See võimaldab koodi jooksutada ilma nt Postgresi serverit installimata, pakkudes samas väga kiiret analüütilist võimekust.
*   **dbt (Data Build Tool):** Kasutatud andmete transformeerimiseks ja modelleerimiseks (Transform). Tagab SQL-koodi modularsuse, testitavuse ja dokumentatsiooni.
*   **Parquet:** Lõpptulemus salvestatakse Parquet failidena, mis on Power BI jaoks optimeeritud ja võimaldab andmeid lugeda ilma andmebaasi draivereid installimata.

---

## 🚀 Kuidas koodi käivitada (Setup)

Eeldused: Arvutis on olemas **Python 3.9+** ja **Git**.

### 1. Projekti allalaadimine ja kausta loomine

Ava terminal (Command Prompt, PowerShell või Terminal) ja käivita järgmised käsud:

```bash
# Loo sobilik kaust ja liigu sinna
mkdir TSK_proovitoo
cd TSK_proovitoo

# Klooni repositoorium
git clone <SINU_GITHUBI_REPO_LINK> .
# NB! Punkt lõpus kloonib failid otse praegusesse kausta
```

### 2. Virtuaalkeskkonna (venv) loomine ja aktiveerimine

Soovituslik on kasutada virtuaalkeskkonda, et vältida teekide konflikte.

```bash
# Loo venv
python -m venv venv

# Aktiveeri venv:
# Windows (PowerShell):
.\venv\Scripts\Activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Sõltuvuste installimine

```bash
pip install -r requirements.txt
```

### 4. ETL protsessi käivitamine

Kogu protsessi (Laadimine -> Transformeerimine -> Eksport) käivitab üks peaskript:

```bash
python main.py
```

**Mida skript teeb?**
1.  **Extract & Load:** Tõmbab TAI API-st andmed ja salvestab need faili `tai_data.duckdb` (tabel `raw_data.tt_osutajad`).
2.  **Transform:** Käivitab `dbt build`, mis loob puhastatud faktitabeli ja dimensioonid (`analytics` skeem).
3.  **Export:** Salvestab lõplikud tabelid kausta `visualiseering/` Parquet formaadis.

---

## 🔍 Andmete kontrollimine (DuckDB)

Kui soovid vaadata andmebaasi sisu ilma Power BI-ta, on projektis kaasas abiskript `debug_db.py`.

```bash
python debug_db.py
```
See skript prindib terminali tabelite nimekirja ja näidised andmetest.

---

## 📊 Visualiseerimine Power BI-s

Kaustas `visualiseering/` asub Power BI fail (`.pbix`) ja genereeritud `.parquet` failid.
Et Power BI leiaks andmed üles sinu arvutis, on failiteede jaoks loodud dünaamiline parameeter.

**Juhis faili avamiseks:**

1.  Ava `.pbix` fail Power BI Desktopis.
2.  Tõenäoliselt näed alguses veateadet, et faile ei leita. See on normaalne.
3.  Mine menüüsse: **Home -> Transform Data -> Edit Parameters**.
4.  Muuda parameetri `ProjectFolderPath` väärtust.
    *   Pane sinna täispikk teekond kaustani, kus asuvad `.parquet` failid.
    *   *Näiteks:* `C:\Users\SinuNimi\Documents\TSK_proovitoo\visualiseering\`
    *   **NB!** Veendu, et lõpus oleks kaldkriips (`\` või `/`).
5.  Vajuta **OK** ja seejärel **Apply Changes**. Graafikud peaksid nüüd uuenema.

---

## 🔄 Andmevoo automaatika (Osa C)

Hetkel käivitub protsess manuaalselt `main.py` skripti kaudu. Tootmiskeskkonnas (Production) oleks lahendus järgmine:

1.  **Orkestreerimine:** Kood pakendatakse Docker konteinerisse ja pannakse jooksma orkestreerimismootoris (nt **Prefect**, **Airflow** või Azure Data Factory).
2.  **Ajastus:** Töö (Job) seadistatakse käivituma igal hommikul kell 04:00 (pärast TAI andmebaaside öist uuendust).
3.  **Inkrementaalsus:** `dlt` võimaldab seadistada inkrementaalset laadimist (laetakse vaid uued andmed), mis muudab protsessi kiiremaks.
4.  **Monitooring:** Vigade korral saadetakse automaatne teavitus (Slack/Email) andmeinsenerile.