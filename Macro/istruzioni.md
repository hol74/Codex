# Istruzioni operative: download indicatori e Web UI

Queste istruzioni descrivono il flusso attuale del progetto.

La Web UI non scarica dati da Internet. I dati esterni si scaricano prima con la CLI, che produce file JSON locali. La Web UI legge poi quei file locali.

## 1. Prerequisiti

Eseguire i comandi dalla root del progetto:

```powershell
cd C:\ProgettiAzure\Codex\Macro
```

La chiave FRED deve essere disponibile in uno di questi modi:

- variabile ambiente `FRED_API_KEY`;
- file `.env` nella root del progetto con:

```text
FRED_API_KEY=la_tua_chiave
```

Il file `.env` deve restare escluso da git.

## 2. Scaricare gli indicatori macro FRED

Per scaricare gli indicatori macro reali al 2026-07-01:

```powershell
dotnet run --project src\MacroRegime.Cli -- --download-fred --as-of 2026-07-01 --fred-source http --output-dir .tmp\data\macro
```

Output atteso:

```text
.tmp\data\macro\macro-data-2026-07-01.json
```

Questo file contiene gli indicatori macro usati dalla baseline della Web UI.

## 3. Avviare la Web UI usando i dati scaricati

Impostare le variabili ambiente per puntare la Web UI al file appena scaricato:

```powershell
$env:MacroRegime__DefaultAsOfDate="2026-07-01"
$env:MacroRegime__DataFilePath="C:\ProgettiAzure\Codex\Macro\.tmp\data\macro\macro-data-2026-07-01.json"
$env:MacroRegime__StrictData="true"
$env:MacroRegime__OutputDirectory="C:\ProgettiAzure\Codex\Macro\.tmp\macro-regime-web"
```

Avviare la Web UI:

```powershell
dotnet run --project src\MacroRegime.Web --urls http://localhost:5117
```

Aprire il browser su:

```text
http://localhost:5117
```

La dashboard calcolera' il regime usando il file FRED locale indicato da `MacroRegime__DataFilePath`.

## 4. Verificare gli input dalla Web UI

Nella Web UI usare la pagina di diagnostica import:

```text
http://localhost:5117/ImportDiagnostics?asOfDate=2026-07-01
```

La diagnostica deve indicare che il file macro data esiste ed e' valido.

## 5. Scaricare anche i market data

I market data non sono ancora usati direttamente dalla dashboard principale. Servono soprattutto per dataset storico, forward returns e Fase E.

Per scaricare market data reali da Yahoo:

```powershell
dotnet run --project src\MacroRegime.Cli -- --download-market-data --as-of 2026-07-01 --market-source yahoo --output-dir .tmp\data\market
```

Output atteso:

```text
.tmp\data\market\market-data-2026-07-01.json
```

## 6. Costruire un dataset storico macro+market

Quando sono disponibili file macro e market per piu' date, si puo' creare un dataset storico con forward returns:

```powershell
dotnet run --project src\MacroRegime.Cli -- --build-historical-dataset --dataset-from 2026-07-01 --dataset-to 2026-07-01 --macro-data-dir .tmp\data\macro --market-data-dir .tmp\data\market --forward-return-days 28,56,91 --output-dir .tmp\data\historical
```

Output atteso:

```text
.tmp\data\historical\historical-dataset-2026-07-01-2026-07-01.json
```

## 7. Spegnere la Web UI

Nel terminale dove gira la Web UI premere:

```text
Ctrl+C
```

