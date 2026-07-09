# Macro Regime - Step 14 Run Manifest Done

Data: 2026-07-08

## Scopo dello step

Step 14 introduce un manifest locale delle run per trasformare la UI da vista della sola run corrente a superficie consultabile nel tempo.

Lo step resta coerente con le decisioni precedenti:

- nessun database;
- nessuna rete runtime;
- persistenza file-based locale;
- Domain invariato;
- Application estesa solo tramite porta;
- Infrastructure responsabile dei dettagli JSON/filesystem;
- Web read-only.

## Cosa e' stato realizzato

### Porta applicativa

E' stata aggiunta la porta:

- `IRegimeRunManifestStore`

Con il record applicativo:

- `RegimeRunManifestEntry`

La entry indicizza:

- as-of date;
- path run JSON;
- path report markdown;
- data source;
- model version;
- feature set version;
- regime primario;
- regime operativo;
- confidence;
- composite score;
- status;
- allocation suggestion;
- turnover;
- estimated cost;
- warning count.

### Run location

`IRegimeRunStore.SaveAsync` ora restituisce la posizione della run salvata.

Questo rende il caso d'uso applicativo capace di registrare nel manifest il path reale della run senza conoscere dettagli di naming o filesystem.

### Manifest JSON locale

E' stato aggiunto:

- `JsonRegimeRunManifestStore`

Il manifest viene scritto in:

- `runs/manifest.json`

Caratteristiche:

- schema version esplicita;
- lettura sicura;
- rifiuto di schema version non supportata;
- upsert per `as-of date`;
- ordinamento decrescente per data;
- nessuna duplicazione se la stessa data viene rieseguita.

### CLI

La CLI ora:

- produce `runs/manifest.json`;
- stampa il path del manifest a fine run.

### Web UI

La dashboard ora mostra una sezione:

- `Run History`

La tabella espone:

- as-of date;
- primary regime;
- operational regime;
- confidence;
- allocation suggestion;
- data source;
- link `Open` per riaprire una data.

La sezione artifact mostra anche:

- path del manifest.

## Verifiche eseguite

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

- `MacroRegime.Domain.Tests`: 79 test superati
- `MacroRegime.Application.Tests`: 17 test superati
- `MacroRegime.Infrastructure.Tests`: 24 test superati
- `MacroRegime.Reporting.Tests`: 2 test superati
- `MacroRegime.Cli.Tests`: 4 test superati
- totale: 126 test superati, 0 falliti

Smoke CLI:

```text
dotnet run --project src\MacroRegime.Cli\MacroRegime.Cli.csproj --no-restore -- --as-of 2026-07-01 --data samples\macro-data-2026-07-01.json --strict-data --model samples\model-version-baseline.json --feature-set samples\feature-set-baseline.json --policy samples\allocation-policy-balanced.json --portfolio samples\current-portfolio-2026-07-01.json --tilts samples\regime-tilt-rules.json --strict-config --output-dir .\.tmp\step14-smoke
```

Esito:

- primary regime: `Goldilocks`;
- operational regime: `Goldilocks`;
- data source: `Imported`;
- allocation suggestion: `PartialRebalance`;
- run JSON generato;
- report markdown generato;
- manifest JSON generato.

Smoke Web:

- `http://localhost:5128` ha risposto `200`;
- pagina contiene `Run History`;
- pagina contiene `Manifest`;
- pagina contiene `Goldilocks`;
- pagina contiene `Imported`;
- pagina contiene `PartialRebalance`.

Gate architetturali:

- nessun riferimento a Web/Infrastructure/Reporting nei layer core;
- nessun uso filesystem concreto in Domain/Application;
- nessun project reference vietato dai progetti core;
- nessuna introduzione di database o HTTP client.

## Cosa resta fuori

Step 14 non introduce:

- database;
- query storiche avanzate;
- confronto visuale tra due run;
- lettura del dettaglio run senza riesecuzione;
- upload/config editing;
- autenticazione;
- provider dati esterni;
- backtesting;
- research lab.

## Valutazione

Step 14 e' completato.

Il sistema ora produce e consulta un indice locale delle run. Questo chiude il limite principale della UI Step 13: la dashboard non e' piu' solo la fotografia della run corrente, ma ha una prima memoria file-based.

La prossima fase consigliata e' un hardening breve prima della chiusura della prima release informativa:

- test Web smoke automatizzato o test di servizio Web;
- visualizzazione della configurazione attiva;
- diagnostica import/config piu' leggibile;
- checkpoint finale della release informativa.
