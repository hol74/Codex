# Macro-Regime plan: Step 7 allocation proposal vincolata

Data: 2026-07-02

## Scopo

Questo documento registra il primo incremento del blocco allocation proposal vincolata, avviato dopo la verifica degli Step 1-6.

La scelta e' coerente con il piano riallineato: prima completare un motore di proposta allocativa prudente e testabile nel dominio, poi collegarlo a report, persistenza, import dati o UI.

## Perimetro

Questo step introduce solo logica di dominio pura.

Sono rimasti fuori scope:

- persistenza;
- EF Core;
- database;
- import dati reali;
- UI;
- report allocation-aware;
- fiscalita' reale dettagliata;
- ottimizzazione di portafoglio avanzata.

## Cosa e' stato implementato

Nuova area di dominio:

```text
src/MacroRegime.Domain/Allocations/
```

Tipi introdotti:

- `AssetClass`
- `AllocationWeight`
- `AllocationBand`
- `PortfolioWeight`
- `CurrentPortfolio`
- `StrategicAllocationPolicy`
- `RegimeTiltRule`
- `DecisionSuggestion`
- `AllocationProposalLine`
- `AllocationProposal`
- `AllocationProposalService`

## Comportamento del servizio

`AllocationProposalService` produce una proposta a partire da:

- `RegimeSnapshot`;
- policy strategica con bande;
- portafoglio corrente;
- regole di tilt per regime;
- costo stimato per turnover.

Il servizio:

- applica solo i tilt del regime operativo;
- sospende i tilt se il regime operativo e' `UncertainTransition`;
- mantiene i target dentro le bande di policy;
- normalizza i target a somma 1;
- calcola turnover come meta' della somma dei trade assoluti;
- scala i trade se il turnover supera il massimo consentito;
- blocca la proposta se il costo stimato supera il massimo di policy;
- restituisce una `DecisionSuggestion`, non una decisione automatica.

## Decisioni modellate

Le decisioni suggerite sono:

- `Hold`;
- `WaitForConfirmation`;
- `PartialRebalance`;
- `FullRebalance`;
- `ManualReviewRequired`.

Questa scelta mantiene la distinzione fra:

- regime detection;
- proposta allocativa;
- decisione umana finale.

## Test aggiunti

Nuovi test:

```text
tests/MacroRegime.Domain.Tests/Allocations/AllocationPolicyTests.cs
tests/MacroRegime.Domain.Tests/Allocations/AllocationProposalServiceTests.cs
```

Copertura introdotta:

- `AllocationWeight` rifiuta valori fuori 0..1;
- `AllocationBand` richiede strategic weight dentro min/max;
- `StrategicAllocationPolicy` rifiuta pesi strategici non normalizzati;
- `CurrentPortfolio` rifiuta duplicati e pesi non normalizzati;
- la proposta applica tilt e resta dentro le bande;
- `UncertainTransition` sospende i tilt e produce `WaitForConfirmation`;
- turnover eccessivo viene scalato al massimo consentito;
- costo stimato eccessivo blocca la proposta e richiede revisione manuale.

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
Application.Tests: 7/7
Reporting.Tests: 1/1
Infrastructure.Tests: 5/5
Totale: 92/92
```

Gate architetturali:

```text
Nessun match per EF, ASP.NET, DbContext, DbSet, HttpClient, SQLite, SqlConnection, DateTime.Now o DateTimeOffset.Now in Domain/Application.
Nessun riferimento a Infrastructure o Reporting da Domain/Application.
Nessun riferimento a file system nei layer core.
```

## Valutazione

Lo step allocation e' completato come primo incremento di dominio.

E' volutamente minimale ma utile:

- non genera portafogli estremi;
- rispetta bande e turnover;
- tratta i costi come vincolo bloccante;
- mantiene `UncertainTransition` come stato operativo reale;
- non confonde proposta con esecuzione.

## Cosa manca

Da fare nei prossimi incrementi:

- collegare la proposta allocativa a un use case Application;
- includere la proposta nel report markdown;
- aggiungere confronto con target precedente o proposta precedente;
- modellare costi piu' granulari per asset class;
- aggiungere vincolo di liquidita';
- aggiungere placeholder fiscale piu' esplicito;
- aggiungere persistenza solo dopo stabilizzazione del contratto applicativo;
- valutare UI solo dopo report e application flow.

## Prossima azione consigliata

Il prossimo passo naturale e' creare un use case Application per generare la proposta allocativa da:

- snapshot regime;
- policy strategica;
- portafoglio corrente;
- regole di tilt.

Questo manterrebbe la logica nel dominio e lascerebbe ad Application solo orchestrazione e contratti.
