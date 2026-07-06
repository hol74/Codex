# Macro Regime - Step 11 Pre-UI Audit

Data: 2026-07-03

## Obiettivo

Audit breve prima della UI, come indicato nello step 10:

- verificare che CLI, import JSON, demo providers e report coprano il flusso minimo desiderato;
- verificare che la composition root locale non rompa i confini architetturali;
- identificare rischi da chiudere prima di esporre i risultati in una dashboard;
- decidere se passare a UI minima o introdurre prima configurazione ulteriore.

## Scope letto

File principali:

- `src/MacroRegime.Cli/Program.cs`;
- `src/MacroRegime.Application/Analysis/RunRegimeAnalysisUseCase.cs`;
- `src/MacroRegime.Application/Regimes/CalculateRegimeUseCase.cs`;
- `src/MacroRegime.Application/Reports/GenerateRegimeReportUseCase.cs`;
- `src/MacroRegime.Infrastructure/Import/JsonDataSnapshotProvider.cs`;
- `src/MacroRegime.Infrastructure/Import/JsonDataSnapshotRecordMapper.cs`;
- `src/MacroRegime.Infrastructure/Persistence/JsonRegimeRunStore.cs`;
- `src/MacroRegime.Infrastructure/Reporting/FileRegimeReportStore.cs`;
- `src/MacroRegime.Infrastructure/Demo/*`;
- `src/MacroRegime.Reporting/Markdown/MarkdownRegimeReportRenderer.cs`;
- test import, analysis, persistence, reporting ed end-to-end.

## Esito sintetico

La slice CLI e' coerente con l'obiettivo dello step 10: permette una pipeline locale senza UI, database o rete runtime, con import JSON opzionale, fallback demo, run JSON e report markdown.

Non emergono bug bloccanti nel codice letto. Prima della UI ci sono pero' tre rischi di prodotto/governance da rendere espliciti:

1. fallback demo troppo silenzioso quando un file JSON non esiste o ha as-of date diversa;
2. assenza di un test diretto dell'entrypoint CLI come contratto operativo;
3. model version, feature set, policy, portfolio e tilt rules restano demo hardcoded.

## Verifiche architetturali

### Confini progetto

Dipendenze osservate:

- `MacroRegime.Domain` non ha project reference;
- `MacroRegime.Application` dipende solo da `MacroRegime.Domain`;
- `MacroRegime.Infrastructure` dipende da `MacroRegime.Application` e `MacroRegime.Domain`;
- `MacroRegime.Reporting` dipende da Application/Domain;
- `MacroRegime.Cli` e' la composition root e dipende da tutti i moduli necessari.

Questo rispetta la direzione desiderata: Domain/Application non conoscono file system, reporting concreto o adapter demo/import.

### No database/rete runtime

Comando eseguito:

```powershell
rg -g '!bin/**' -g '!obj/**' "(EntityFramework|DbContext|SqlConnection|HttpClient|Dapper|Npgsql|Sqlite|DateTime\.Now|DateTime\.UtcNow)" src tests
```

Esito:

- nessun match nei sorgenti/test non generati.

Nota: una ricerca non filtrata trova riferimenti a `System.Net.Http` dentro `obj/` e global usings generati dal test SDK; non sono uso applicativo.

## Osservazioni tecniche

### 1. Fallback demo su file mancante o as-of mismatch

In `JsonDataSnapshotProvider`, se il file non esiste viene usato il fallback:

- `src/MacroRegime.Infrastructure/Import/JsonDataSnapshotProvider.cs`, righe 28-31.

Se il file esiste ma contiene un `asOfDate` diverso da quello richiesto, viene ancora usato il fallback:

- `src/MacroRegime.Infrastructure/Import/JsonDataSnapshotProvider.cs`, righe 51-55.

La CLI passa sempre `DemoDataSnapshotProvider` come fallback quando viene indicato `--data`:

- `src/MacroRegime.Cli/Program.cs`, righe 83-89.

I test confermano questo comportamento:

- `tests/MacroRegime.Infrastructure.Tests/Import/JsonDataSnapshotProviderTests.cs`, righe 88-115.

Valutazione: accettabile per Step 10 e per smoke locale. Rischioso per UI/utente finale, perche' una dashboard potrebbe mostrare output "riuscito" anche quando il dato importato non e' stato usato.

Decisione consigliata: prima della UI aggiungere un segnale esplicito sull'origine del dato (`Imported`, `DemoFallback`, `EmptyFallback`) o una modalita' CLI `--strict-data` che fallisce se `--data` e' mancante/non coerente.

### 2. Snapshot vuoto se provider non restituisce dati

`CalculateRegimeUseCase` trasforma un provider null in snapshot vuoto:

- `src/MacroRegime.Application/Regimes/CalculateRegimeUseCase.cs`, righe 49-50.

Valutazione: utile per rendere il detector robusto a dati mancanti, ma da governare. Uno snapshot vuoto puo' produrre `UncertainTransition` con warning, ma per UI dovrebbe essere chiaramente distinguibile da un run completo.

Decisione consigliata: mantenere il comportamento nel dominio/app layer, ma far emergere nel report/UI un indicatore di completezza input e/o numero feature mancanti.

### 3. CLI non testata come entrypoint

Sono presenti buoni test su import, pipeline applicativa, store JSON/report e end-to-end locale. Non e' presente un test che lanci direttamente `MacroRegime.Cli` o che verifichi parsing/exit code dell'entrypoint.

Valutazione: non bloccante per andare avanti, ma il comando CLI e' il contratto operativo temporaneo fino alla UI.

Decisione consigliata: aggiungere nello step successivo un test smoke CLI o almeno testare `MacroRegimeCli.RunAsync` rendendo visibile l'internal alla test assembly. In alternativa mantenere smoke manuale documentato fino a quando arriva la UI.

### 4. Configurazione ancora demo-hardcoded

La composition root CLI usa provider demo per:

- model version;
- feature set;
- strategic allocation policy;
- current portfolio;
- tilt rules.

Riferimento:

- `src/MacroRegime.Cli/Program.cs`, righe 35-47.

Valutazione: coerente con il verticale minimo. Non e' ancora adatto a una UI che sembri parametrizzabile o "reale".

Decisione consigliata: prima o insieme alla UI minima, introdurre almeno un chiaro badge "Demo policy/config" oppure caricare da file JSON anche model/feature/policy/portfolio. La scelta dipende da quanto la prima UI deve essere demo viewer o strumento operativo personale.

## Verifiche eseguite

### Ambiente .NET

Comandi:

```powershell
dotnet --list-sdks
dotnet --info
```

Esito:

- SDK installati: 2.1.x, 3.1.x, 8.0.421, 9.0.314;
- nessun SDK .NET 10 installato;
- nessun `global.json` nel repository.

### Build

Comando:

```powershell
dotnet build MacroRegime.slnx --no-restore
```

Esito:

- fallita per errore ambientale `NETSDK1045`;
- SDK corrente: 9.0.314;
- i progetti targettano `net10.0`;
- 9 errori, 0 warning.

Interpretazione: non e' una regressione del codice auditato, ma la workstation corrente non puo' ricostruire la solution finche' non e' disponibile .NET SDK 10 o non si decide esplicitamente di retargettare a .NET 9.

## Decisione

La slice Step 10 e' architetturalmente pronta per una UI minima solo come dashboard demo/local-run viewer, a condizione che la UI esponga chiaramente:

- data source effettiva;
- presenza di fallback demo;
- versioni demo di modello/feature/policy;
- warning e feature mancanti.

Se invece la prossima UI deve essere gia' vicina all'uso operativo personale, conviene prima fare uno Step 12 di configurazione locale:

- data source strict opzionale;
- model/feature/policy/portfolio da JSON;
- indicatore input completeness;
- smoke test CLI.

## Prossima azione consigliata

Step 12 consigliato: "local governance/config before UI".

Deliverable minimo:

- aggiungere tracciamento origine dati nel risultato/report;
- aggiungere modalita' strict per `--data`;
- aggiungere smoke test CLI o test parsing/exit code;
- decidere se mantenere `net10.0` richiedendo SDK 10 o introdurre `global.json`/retargeting esplicito.

Solo dopo, Step 13: UI minima sobria su run/report gia' prodotti.
