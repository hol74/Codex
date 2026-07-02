# ADR 0002: Regole di dipendenza fra layer

Data: 2026-07-02

Status: Accepted

## Contesto

Il Macro-Regime Engine deve separare calcolo, orchestrazione, persistenza, reportistica e UI. Il primo tentativo Finance aveva una struttura nominalmente separata, ma la logica critica del regime viveva in Infrastructure e dipendeva da EF Core.

Questo ADR definisce le regole di dipendenza per il nuovo sistema.

## Decisione

Il nuovo sistema usera' questa struttura logica:

```text
MacroRegime.Domain
MacroRegime.Application
MacroRegime.Infrastructure
MacroRegime.Reporting
MacroRegime.Web
```

Le dipendenze consentite sono:

```text
Application -> Domain
Infrastructure -> Application
Infrastructure -> Domain
Reporting -> Application
Reporting -> Domain
Web -> Application
Web -> Infrastructure
Web -> Reporting
```

`Domain` non dipende da nessun altro layer.

## Regole per Domain

`MacroRegime.Domain` contiene:

- value object;
- enum e tipi di dominio;
- record/aggregate puri;
- servizi di dominio puri;
- invarianti;
- errori di dominio;
- calcoli deterministici.

`MacroRegime.Domain` non puo' contenere:

- EF Core;
- DbContext;
- DbSet;
- navigation properties;
- ASP.NET;
- controller;
- Razor;
- HTTP client;
- file system;
- database;
- clock di sistema;
- logging infrastrutturale;
- configurazione runtime.

Esempio consentito:

```text
BaselineRegimeDetector.Detect(featureScores, modelVersion)
```

Esempio vietato:

```text
BaselineRegimeDetector.Detect(FinanceDbContext dbContext, DateOnly asOfDate)
```

## Regole per Application

`MacroRegime.Application` contiene:

- use case;
- command/query model;
- porte verso persistenza e dati esterni;
- DTO applicativi;
- orchestrazione;
- validazioni di flusso;
- warnings applicativi.

Application puo':

- dipendere da Domain;
- definire interfacce repository;
- definire interfacce snapshot provider;
- orchestrare detector e normalizer.

Application non deve:

- implementare EF Core;
- chiamare direttamente HTTP provider reali;
- conoscere dettagli SQLite;
- generare HTML della UI;
- nascondere logica di dominio nei DTO.

Esempio consentito:

```text
CalculateRegimeUseCase.Execute(command)
```

Esempio vietato:

```text
CalculateRegimeUseCase.Execute(command) chiama direttamente DbContext.SaveChangesAsync()
```

## Regole per Infrastructure

`MacroRegime.Infrastructure` contiene:

- EF Core;
- repository concreti;
- import FRED/ALFRED/FRED-MD;
- file provider;
- database provider;
- implementazioni di clock;
- implementazioni delle porte Application.

Infrastructure puo':

- dipendere da Application;
- dipendere da Domain;
- mappare entita' persistenti a tipi di dominio;
- salvare run, snapshot, feature e report.

Infrastructure non deve:

- decidere regimi;
- contenere formule del baseline detector;
- creare output di dominio senza passare dai servizi di dominio;
- diventare il luogo primario della logica.

## Regole per Reporting

`MacroRegime.Reporting` contiene:

- generazione Markdown;
- generazione HTML statico;
- generazione JSON report;
- formatting leggibile;
- template di report.

Reporting puo':

- leggere output applicativi;
- formattare narrative;
- produrre file o stringhe tramite adapter controllati.

Reporting non deve:

- calcolare il regime;
- interrogare direttamente database;
- decidere allocazioni.

## Regole per Web

`MacroRegime.Web` contiene:

- controller;
- view model;
- Razor views;
- routing;
- configurazione UI;
- binding input utente.

Web puo':

- chiamare use case Application;
- mostrare report;
- usare Infrastructure via dependency injection;
- mostrare stato e warnings.

Web non deve:

- calcolare feature;
- calcolare probabilita';
- persistere run direttamente;
- contenere formule di regime.

## Dipendenze vietate

Sono sempre vietate:

- `Domain -> Application`
- `Domain -> Infrastructure`
- `Domain -> Web`
- `Application -> Infrastructure`
- `Application -> Web`
- `Infrastructure` come sede del detector baseline
- `Web` come sede di logica di regime

## Test di accettazione architetturale

Prima di completare lo scheletro:

- `MacroRegime.Domain.csproj` non deve avere `PackageReference` a EF Core.
- `MacroRegime.Domain.csproj` non deve avere riferimenti ASP.NET.
- `MacroRegime.Application.csproj` non deve referenziare Infrastructure.
- I test Domain devono istanziare il detector senza database.
- I test Application devono usare porte fake/in-memory.

## Conseguenze positive

- Il core resta stabile e testabile.
- Infrastructure puo' cambiare senza riscrivere il detector.
- La UI puo' evolvere senza alterare la logica.
- I challenger model possono essere aggiunti dietro contratti.

## Conseguenze negative

- Serve piu' mapping fra entita' persistenti e dominio.
- Alcuni use case richiederanno DTO espliciti.
- Lo sviluppo iniziale e' piu' disciplinato e meno rapido.

## Note operative per Codex

Quando Codex crea o modifica codice:

1. Deve controllare il progetto di destinazione.
2. Deve evitare riferimenti Infrastructure in Domain/Application.
3. Deve preferire test puri prima di adapter.
4. Deve segnalare ogni violazione di dipendenza come blocco architetturale.
