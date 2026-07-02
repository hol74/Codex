# Macro-Regime plan: Step 7 vertical slice locale

Data: 2026-07-02

## Scopo

Questo documento registra l'incremento che chiude una vertical slice locale della prima scrittura:

```text
regime snapshot -> allocation proposal -> markdown report -> file locali
```

La slice resta senza rete, senza database e senza UI.

## Cosa e' stato aggiunto

Nuova area Application:

```text
src/MacroRegime.Application/Analysis/
```

Artefatti:

- `RunRegimeAnalysisCommand`
- `RunRegimeAnalysisResult`
- `RunRegimeAnalysisUseCase`

Il nuovo use case orchestra use case gia' esistenti:

- `CalculateRegimeUseCase`
- `GenerateAllocationProposalUseCase`
- `GenerateRegimeReportUseCase`

## Comportamento

`RunRegimeAnalysisUseCase`:

1. calcola il regime as-of date;
2. interrompe il flusso se il calcolo regime fallisce;
3. genera la proposta allocativa vincolata;
4. interrompe il flusso se manca policy/portfolio o se la proposta fallisce;
5. genera il report markdown con snapshot e allocation proposal;
6. salva il report usando la porta `IRegimeReportStore`;
7. restituisce snapshot, proposta, markdown e location del report.

Il salvataggio del run resta responsabilita' opzionale di `CalculateRegimeUseCase` tramite `IRegimeRunStore`.

## Cosa non e' stato introdotto

Non sono stati introdotti:

- database;
- EF Core;
- import reali;
- HTTP;
- UI;
- nuovi adapter esterni;
- logica di dominio dentro Application;
- logica di report dentro Domain.

## Test aggiunti

Application:

```text
tests/MacroRegime.Application.Tests/Analysis/RunRegimeAnalysisUseCaseTests.cs
```

Copertura:

- pipeline completa regime -> allocation -> report;
- failure quando manca model version;
- failure quando manca strategic allocation policy;
- il report non viene salvato se il flusso fallisce prima.

Infrastructure end-to-end:

```text
tests/MacroRegime.Infrastructure.Tests/EndToEnd/RegimeRunAndReportEndToEndTests.cs
```

Copertura aggiunta:

- `RunRegimeAnalysisUseCase`;
- provider fake in memoria;
- `JsonRegimeRunStore`;
- `FileRegimeReportStore`;
- `MarkdownRegimeReportRenderer`;
- verifica file run JSON;
- verifica file report markdown allocation-aware.

## Verifiche

Build:

```text
dotnet build MacroRegime.slnx --no-restore
Warning: 0
Errori: 0
```

Test:

```text
dotnet test MacroRegime.slnx --no-restore
Domain.Tests: 79/79
Application.Tests: 16/16
Reporting.Tests: 2/2
Infrastructure.Tests: 6/6
Totale: 103/103
```

Gate architetturali:

```text
Nessun match per EF, ASP.NET, DbContext, DbSet, HttpClient, SQLite, SqlConnection, DateTime.Now o DateTimeOffset.Now in Domain/Application.
Nessun riferimento a Infrastructure o Reporting da Domain/Application.
Nessun riferimento a file system nei layer core.
```

## Valutazione

Questo incremento completa una prima slice applicativa utile e coerente:

- il dominio resta puro;
- Application orchestra;
- Reporting formatta;
- Infrastructure salva file locali;
- la pipeline e' testata end-to-end senza rete/database.

La prima scrittura non e' ancora completa, ma ora esiste un flusso informativo dimostrabile.

## Prossima azione consigliata

Prima di aggiungere UI o database, conviene fare un audit di Step 7:

- verificare completezza di allocation domain;
- verificare coerenza Application/Reporting;
- controllare duplicazione fixture;
- decidere se introdurre adapter Infrastructure per policy/portfolio/tilt demo;
- decidere se il prossimo passo sia data/import oppure UI minima.
