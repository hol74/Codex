# Macro-Regime plan: Step 7 reporting allocation-aware

Data: 2026-07-02

## Scopo

Questo documento registra l'incremento che collega la proposta allocativa al report markdown.

La logica di allocation resta nel dominio. Application costruisce il contenuto del report. Reporting formatta il contenuto in markdown.

## Perimetro

Incluso:

- contenuto report con `RegimeSnapshot` e `AllocationProposal` opzionale;
- command report aggiornato per accettare una proposta allocativa;
- renderer markdown con sezione `Allocation Proposal`;
- test del renderer con e senza allocation;
- end-to-end locale con run JSON e report markdown allocation-aware.

Escluso:

- persistenza dedicata della proposta allocativa;
- database;
- UI;
- report HTML;
- cost model avanzato;
- fiscalita' reale.

## Artefatti modificati

Application:

- `RegimeReportContent`
- `GenerateRegimeReportCommand`
- `GenerateRegimeReportUseCase`
- `IRegimeReportRenderer`

Reporting:

- `MarkdownRegimeReportRenderer`

Test:

- `GenerateRegimeReportUseCaseTests`
- `MarkdownRegimeReportRendererTests`
- `RegimeRunAndReportEndToEndTests`

## Comportamento

`RegimeReportContent` contiene:

- snapshot regime obbligatorio;
- proposta allocativa opzionale.

Se la proposta allocativa e' presente, la sua as-of date deve coincidere con quella dello snapshot.

Il renderer markdown ora include:

- decision suggestion;
- turnover;
- estimated cost;
- tabella asset class/current/strategic/target/trade/band/tilt;
- rationale;
- constraint messages.

Se la proposta non e' disponibile, il report resta valido e scrive:

```text
No allocation proposal available.
```

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
Application.Tests: 13/13
Reporting.Tests: 2/2
Infrastructure.Tests: 5/5
Totale: 99/99
```

Gate architetturali:

```text
Nessun match per EF, ASP.NET, DbContext, DbSet, HttpClient, SQLite, SqlConnection, DateTime.Now o DateTimeOffset.Now in Domain/Application.
Nessun riferimento a Infrastructure o Reporting da Domain/Application.
Nessun riferimento a file system nei layer core.
```

## Valutazione

L'incremento e' coerente con il piano:

- il dominio calcola;
- Application orchestra;
- Reporting formatta;
- Infrastructure salva solo file gia' prodotti;
- nessuna UI e nessun database sono stati anticipati.

## Prossima azione consigliata

Il prossimo incremento naturale e' chiudere una vertical slice applicativa locale:

1. regime snapshot;
2. allocation proposal;
3. markdown report;
4. salvataggio file locale;
5. test end-to-end senza rete/database.

La parte piu' importante sara' evitare duplicazione di fixture e introdurre un orchestratore applicativo solo se riduce complessita' reale.
