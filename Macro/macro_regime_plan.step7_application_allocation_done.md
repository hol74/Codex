# Macro-Regime plan: Step 7 Application allocation proposal

Data: 2026-07-02

## Scopo

Questo documento registra il secondo incremento dello Step 7 allocation proposal vincolata.

Il primo incremento ha introdotto il motore di dominio puro in:

```text
src/MacroRegime.Domain/Allocations/
```

Questo incremento rende quel motore invocabile dall'Application layer tramite porte e use case, senza introdurre persistenza, UI o adapter reali.

## Perimetro

Incluso:

- porte Application per recuperare policy strategica, portafoglio corrente e tilt rules;
- command/result applicativi;
- use case per generare la proposta allocativa;
- test Application con provider fake.

Escluso:

- salvataggio della proposta;
- report markdown allocation-aware;
- end-to-end report con allocation;
- adapter Infrastructure reali;
- database;
- UI.

## Artefatti aggiunti

Porte:

- `IStrategicAllocationPolicyProvider`
- `ICurrentPortfolioProvider`
- `IRegimeTiltRuleProvider`

Use case:

- `GenerateAllocationProposalCommand`
- `GenerateAllocationProposalResult`
- `GenerateAllocationProposalUseCase`

Test:

- `GenerateAllocationProposalCommandTests`
- `GenerateAllocationProposalUseCaseTests`
- `AllocationProposalTestFixtures`

## Comportamento

`GenerateAllocationProposalUseCase`:

1. riceve un `RegimeSnapshot`;
2. usa l'as-of date dello snapshot;
3. recupera la policy strategica tramite porta;
4. recupera il portafoglio corrente tramite porta;
5. recupera le regole di tilt tramite porta;
6. chiama `AllocationProposalService`;
7. restituisce `GenerateAllocationProposalResult`.

Il use case non calcola direttamente bande, turnover, costi o suggerimenti. Quella logica resta nel dominio.

## Error handling

Il use case restituisce failure quando:

- manca la strategic allocation policy;
- manca il portafoglio corrente.

Le tilt rules possono essere vuote: in quel caso il dominio produce una proposta coerente con la policy, normalmente `Hold` se il portafoglio e' gia' strategico.

## Test aggiunti

Copertura:

- command rifiuta snapshot nullo;
- command rifiuta costo stimato negativo;
- use case genera proposta da provider in memoria;
- use case passa l'as-of date dello snapshot ai provider;
- use case fallisce se manca la policy;
- use case fallisce se manca il portafoglio;
- use case gestisce lista tilt vuota.

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
Reporting.Tests: 1/1
Infrastructure.Tests: 5/5
Totale: 98/98
```

Gate architetturali:

```text
Nessun match per EF, ASP.NET, DbContext, DbSet, HttpClient, SQLite, SqlConnection, DateTime.Now o DateTimeOffset.Now in Domain/Application.
Nessun riferimento a Infrastructure o Reporting da Domain/Application.
Nessun riferimento a file system nei layer core.
```

## Valutazione

L'incremento e' coerente con il piano riallineato.

La sequenza ora e':

1. dominio allocation vincolato e testato;
2. use case Application che orchestra quel dominio;
3. prossimo incremento: includere la proposta allocativa nel reporting.

Non abbiamo anticipato Infrastructure o UI. Questo mantiene il sistema vicino alla governance e lontano dall'errore del prototipo Finance, dove calcolo, persistenza e presentazione erano troppo accoppiati.

## Prossima azione consigliata

Estendere il reporting in modo controllato:

- introdurre un renderer/report command che accetti anche `AllocationProposal`;
- aggiungere una sezione markdown "Allocation proposal";
- testare report con regime snapshot + proposta;
- solo dopo aggiornare l'end-to-end locale.
