# Macro Regime - Step 9 Data Import Done

Data: 2026-07-02

## Obiettivo

Passare a data/import locale senza introdurre database, rete o UI.

Lo step richiedeva:

- definire record di input importabile;
- implementare un file adapter deterministico per `IDataSnapshotProvider`;
- validare schema/versione del file importato;
- mantenere i provider demo come fallback o scenario smoke test.

## Fatto

Sono stati aggiunti i record importabili in `MacroRegime.Infrastructure.Import`:

- `JsonDataSnapshotRecord`;
- `JsonMacroObservationRecord`;
- `JsonMarketObservationRecord`.

E' stato aggiunto il mapper:

- `JsonDataSnapshotRecordMapper`.

Il mapper valida:

- `SchemaVersion` uguale alla versione corrente;
- `AsOfDate` presente;
- array `MacroObservations` presente;
- array `MarketObservations` presente;
- codici, nomi e dimensioni economiche obbligatorie;
- date obbligatorie per osservazioni macro e market;
- dimensioni economiche parseabili verso `EconomicDimension`.

E' stato aggiunto il provider:

- `JsonDataSnapshotProvider`.

Comportamento del provider:

- legge un singolo file JSON locale;
- deserializza con `System.Text.Json` e `JsonSerializerDefaults.Web`;
- converte il record in `DataSnapshot`;
- se il file non esiste usa il fallback provider, se configurato;
- se il file esiste ma l'as-of date non corrisponde alla richiesta usa il fallback provider, se configurato;
- se il file esiste ma e' corrotto, vuoto o con schema non supportato fallisce esplicitamente con `InvalidDataException`.

Questa scelta evita di mascherare dati importati sbagliati con il demo provider.

## Schema JSON v1

Forma attesa:

```json
{
  "schemaVersion": 1,
  "asOfDate": "2026-07-01",
  "macroObservations": [
    {
      "seriesCode": "ISM_PMI",
      "name": "ISM manufacturing PMI",
      "dimension": "Growth",
      "observationDate": "2026-06-30",
      "publicationDate": "2026-07-01",
      "vintageDate": "2026-07-01",
      "value": 55.0,
      "source": "Local",
      "unit": "Index"
    }
  ],
  "marketObservations": []
}
```

Dimensioni accettate:

- `Growth`;
- `Inflation`;
- `Risk`;
- `Monetary`;
- `Credit`;
- `Liquidity`;
- `Sentiment`.

## Test aggiunti

Aggiunto `JsonDataSnapshotProviderTests` con copertura su:

- lettura di file import v1 valido;
- errore su schema version non supportata;
- errore su campo obbligatorio mancante;
- fallback demo quando il file manca;
- fallback demo quando l'as-of date del file non corrisponde;
- pipeline completa con `JsonDataSnapshotProvider`, provider demo restanti, JSON run store e markdown report store.

## Verifiche

Comandi eseguiti:

```powershell
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore
rg -n "EntityFramework|AspNetCore|DbContext|DbSet|HttpClient|Sqlite|SqlConnection|DateTime\.Now|DateTimeOffset\.Now" src\MacroRegime.Domain src\MacroRegime.Application --glob '!**/bin/**' --glob '!**/obj/**'
rg -n "MacroRegime.Infrastructure|MacroRegime.Reporting|File\.|Directory\.|Path\." src\MacroRegime.Domain src\MacroRegime.Application --glob '!**/bin/**' --glob '!**/obj/**'
rg -n "ProjectReference Include=.*MacroRegime.Infrastructure|ProjectReference Include=.*MacroRegime.Reporting" src\MacroRegime.Domain src\MacroRegime.Application tests\MacroRegime.Domain.Tests tests\MacroRegime.Application.Tests --glob '*.csproj'
rg -n "HttpClient|WebRequest|Sqlite|SqlConnection|DbContext|DbSet|EntityFramework" src tests --glob '!**/bin/**' --glob '!**/obj/**'
```

Risultati:

- build: superata, 0 warning, 0 errori;
- test: superati 111/111;
- Domain/Application: nessuna dipendenza da file system, Infrastructure, Reporting, database, web o clock impliciti;
- rete/database: nessun uso di HTTP, EF o SQL.

## Decisione architetturale

Il formato import e' Infrastructure-specific: Domain e Application continuano a vedere solo `DataSnapshot` e `IDataSnapshotProvider`.

Il fallback demo e' esplicito tramite composizione:

```csharp
new JsonDataSnapshotProvider(filePath, new DemoDataSnapshotProvider())
```

Questo permette tre modalita':

- import obbligatorio: provider senza fallback;
- import con fallback demo: provider con `DemoDataSnapshotProvider`;
- smoke test demo puro: `DemoDataSnapshotProvider` senza file import.

## Prossimo passo consigliato

Prima della UI resta utile un piccolo incremento di hardening:

- aggiungere un provider file-based analogo per model/feature set solo se vogliamo renderli configurabili;
- oppure introdurre una piccola composition root console/CLI locale che esegua la pipeline con provider JSON + demo fallback.

La UI resta dopo: ora la pipeline ha gia' un ingresso dati locale verificabile.
