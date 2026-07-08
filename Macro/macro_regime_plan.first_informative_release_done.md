# Macro Regime - First Informative Release Done

Data: 2026-07-08

## Decisione

La prima release informativa del progetto Macro-Regime e' completata.

Questa release non e' un prodotto quantitativo avanzato e non pretende di essere un motore predittivo definitivo. E' la prima versione applicativa governata, locale, riproducibile e consultabile del sistema:

- calcola una baseline rule-based;
- produce probabilita' di regime;
- espone driver e segnali contrari;
- genera una proposta allocativa vincolata;
- salva run e report;
- indicizza lo storico locale delle run;
- rende il risultato consultabile via CLI e Web UI.

## Nota sul piano originario

Il piano `macro_regime_plan.md` resta valido come visione complessiva, ma la prima implementazione e' stata riallineata dal post-mortem e dal restart architetturale.

La differenza principale e' questa:

- il piano originario citava una prima persistenza applicativa anche in chiave EF Core;
- dopo il restart abbiamo scelto consapevolmente una prima release file-based, senza database, per proteggere dominio, testabilita', as-of semantics e audit trail.

Quindi la prima release rispetta lo spirito del piano, ma non implementa ancora la persistenza database. La scelta e' intenzionale e documentata nei checkpoint precedenti.

## Scope completato

### Domain

Completato:

- value object temporali;
- probabilita' e score normalizzati;
- tipi regime;
- feature definition;
- feature score;
- feature set version;
- model version;
- regime snapshot;
- explanation;
- baseline rule-based detector;
- normalizzazione probabilita';
- composite score;
- allocation domain;
- policy, bande, portfolio, tilt e proposal.

### Application

Completato:

- use case di calcolo regime;
- use case di proposta allocativa;
- use case di generazione report;
- vertical slice `RunRegimeAnalysisUseCase`;
- porte applicative per dati, config, run store, report renderer/store e manifest run;
- gestione data source info;
- output con run location e report location.

### Infrastructure

Completato:

- provider demo deterministici;
- import locale JSON per dati macro/market;
- import locale JSON per model version, feature set, policy, portfolio e tilt rules;
- validazione schema/versione;
- fallback demo controllato;
- strict data/config;
- store JSON idempotente delle run;
- manifest JSON locale delle run;
- file report store markdown.

### Reporting

Completato:

- renderer markdown;
- report con regime, probabilita', feature, driver, warning, data source e allocation proposal.

### CLI

Completato:

- run end-to-end locale;
- parametri per data/config JSON;
- `--strict-data`;
- `--strict-config`;
- output run JSON;
- output report markdown;
- output manifest run.

### Web UI

Completato:

- dashboard read-only;
- as-of date selector;
- regime summary;
- data source;
- probabilita' regime;
- feature scores;
- explanations;
- allocation proposal;
- rationale e constraints;
- warning;
- artifact paths;
- report markdown;
- run history;
- active configuration con path risolti e stato file.

## Verifiche finali

Build:

```text
dotnet build MacroRegime.slnx --no-restore
```

Esito:

- build superata;
- 0 warning;
- 0 errori.

Test:

```text
dotnet test MacroRegime.slnx --no-restore
```

Esito:

- `MacroRegime.Domain.Tests`: 79 test superati;
- `MacroRegime.Application.Tests`: 17 test superati;
- `MacroRegime.Infrastructure.Tests`: 24 test superati;
- `MacroRegime.Reporting.Tests`: 2 test superati;
- `MacroRegime.Cli.Tests`: 4 test superati;
- totale: 126 test superati, 0 falliti.

Smoke CLI:

- run completata;
- primary regime: `Goldilocks`;
- operational regime: `Goldilocks`;
- data source: `Imported`;
- allocation suggestion: `PartialRebalance`;
- run JSON generato;
- report markdown generato;
- run manifest generato.

Smoke Web:

- `http://localhost:5128` ha risposto `200`;
- pagina contiene `Macro Regime`;
- pagina contiene `Run History`;
- pagina contiene `Active configuration`;
- pagina contiene `Found`;
- pagina contiene `Manifest`;
- pagina contiene `Goldilocks`;
- pagina contiene `PartialRebalance`.

Gate architetturali:

- Domain e Application non dipendono da Web, Infrastructure o Reporting concreto;
- Domain e Application non usano filesystem concreto;
- nessun database introdotto;
- nessuna rete runtime introdotta;
- nessun project reference vietato nei core layer.

## Definition of Done della prima release

Completata:

- solution C# compilabile;
- dominio testato;
- baseline rule-based funzionante;
- run demo riproducibile;
- import/config locale governato;
- audit/as-of semantics minime;
- probabilita' di regime;
- driver e segnali contrari;
- stato incerto gestito;
- allocation proposal vincolata;
- report leggibile;
- CLI operativa;
- Web UI read-only;
- storico run locale;
- documentazione aggiornata;
- test automatici verdi.

## Cosa resta fuori

Restano fuori dalla prima release:

- database;
- EF Core;
- provider dati esterni FRED/ALFRED;
- import storico esteso;
- backtesting;
- walk-forward;
- stress test;
- HMM, clustering, Markov switching e jump model;
- research lab Python;
- autenticazione;
- upload file;
- editing configurazione da UI;
- confronto visuale tra run;
- fiscalita' reale dettagliata;
- esecuzione ordini;
- trading automatico.

## Rischi residui

- La UI Web e' verificata con smoke HTTP/manuale strutturato, ma non ha ancora un progetto test Web dedicato.
- Il manifest locale indicizza le run, ma il dettaglio storico riapre la data rieseguendo la pipeline invece di leggere direttamente un record passato.
- I sample locali sono utili per governance e demo, ma non rappresentano ancora un dataset macro storico reale.
- La diagnostica import/config e' leggibile, ma non ancora formalizzata come report di validazione separato.

## Stato della release

La prima release informativa e' pronta.

La prossima fase non dovrebbe aggiungere subito complessita' quantitativa. La direzione consigliata e':

1. consolidare storico e confronto run;
2. migliorare import dati e diagnostica;
3. decidere se introdurre database locale;
4. solo dopo aprire research lab e modelli challenger.

In altre parole: prima rendere il sistema informativo piu' affidabile nel tempo, poi renderlo piu' sofisticato.
