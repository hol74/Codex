# Macro Regime - Step 13 UI Done

Data: 2026-07-06

## Scopo dello step

Step 13 aveva l'obiettivo di introdurre una UI minima, locale e read-only per consultare una run macro-regime prodotta dalla pipeline gia' costruita negli step precedenti.

Il criterio guida era: rendere visibile il sistema senza cambiare la sua architettura. La UI doveva essere un adapter esterno, non un nuovo luogo in cui mettere logica di dominio.

## Cosa e' stato realizzato

E' stato creato il progetto:

- `src/MacroRegime.Web`

Il progetto e' stato aggiunto a:

- `MacroRegime.slnx`

Il progetto Web dipende dai layer gia' previsti:

- `MacroRegime.Application`
- `MacroRegime.Domain`
- `MacroRegime.Infrastructure`
- `MacroRegime.Reporting`

La pagina principale e' una dashboard operativa, non una landing page. La prima schermata permette di:

- scegliere una `as-of date`;
- lanciare una run locale;
- vedere il regime primario e il regime operativo;
- vedere confidence, composite score e data source;
- vedere model version e feature set version;
- consultare probabilita' dei regimi;
- consultare feature score;
- consultare driver e segnali contrari;
- consultare warning;
- consultare proposta allocativa;
- vedere rationale, constraints, turnover e costo stimato;
- vedere i path degli artifact generati;
- leggere il report markdown generato.

## Configurazione

La UI usa configurazione ASP.NET standard tramite:

- `src/MacroRegime.Web/appsettings.json`

I default puntano ai sample locali introdotti negli step precedenti:

- `samples/macro-data-2026-07-01.json`
- `samples/model-version-baseline.json`
- `samples/feature-set-baseline.json`
- `samples/allocation-policy-balanced.json`
- `samples/current-portfolio-2026-07-01.json`
- `samples/regime-tilt-rules.json`

L'output Web locale viene scritto in:

- `.tmp/macro-regime-web`

Le chiavi Data Protection locali vengono persistite in:

- `.tmp/macro-regime-web-keys`

Questa scelta evita warning rumorosi di runtime e resta coerente con lo scope locale dello step.

## Verifica rispetto al piano

### Step 13a - Web skeleton

Completato.

- `MacroRegime.Web` esiste.
- Il progetto e' nella solution.
- La dashboard e' raggiungibile.
- La UI ha layout sobrio e operativo.

### Step 13b - Run orchestration web

Completato.

- La Web UI compone la pipeline tramite un servizio applicativo Web.
- I path vengono letti da configurazione.
- La run viene eseguita per la `as-of date` selezionata.
- Vengono generati artifact JSON e markdown report.
- Gli errori operativi vengono mostrati in pagina.

### Step 13c - Dashboard result

Completato.

- Regime summary visibile.
- Probabilita' visibili e ordinate.
- Feature score visibili.
- Driver, segnali contrari e warning visibili.
- Layout verificato su desktop e mobile.

### Step 13d - Allocation panel

Completato.

- Allocation proposal visibile.
- Decision suggestion visibile.
- Turnover e costo stimato visibili.
- Rationale e constraints visibili.

### Step 13e - Verification and checkpoint

Completato con questo documento.

## Verifiche eseguite

Build e test:

```text
dotnet test MacroRegime.slnx --no-restore
```

Esito:

- `MacroRegime.Domain.Tests`: 79 test superati
- `MacroRegime.Application.Tests`: 16 test superati
- `MacroRegime.Infrastructure.Tests`: 20 test superati
- `MacroRegime.Reporting.Tests`: 2 test superati
- `MacroRegime.Cli.Tests`: 4 test superati
- totale: 121 test superati, 0 falliti

Smoke HTTP:

- `http://localhost:5128` risponde `200`
- la pagina contiene `Macro Regime`
- la pagina contiene `Goldilocks`
- la pagina contiene `Imported`
- la pagina contiene `PartialRebalance`
- la pagina contiene `Regime Probabilities`
- la pagina contiene `Allocation Proposal`

Verifica browser desktop:

- CSS caricato da `/css/site.css`
- layout tabellare stabile
- contenuti principali visibili
- nessun overflow orizzontale incoerente rilevato

Verifica browser mobile:

- viewport verificato a 390x844
- body e document width coerenti con la viewport
- tabelle contenute nei rispettivi wrapper
- contenuti principali visibili

Gate architetturali:

- nessun riferimento a `MacroRegime.Web`, `MacroRegime.Infrastructure`, `MacroRegime.Reporting`, filesystem o path concreti in `MacroRegime.Domain` e `MacroRegime.Application`
- nessun project reference vietato verso Web/Infrastructure/Reporting nei progetti core e nei test core
- nessun uso di database, Entity Framework, SQLite, SQL connection o chiamate HTTP nei layer controllati per questo step

## Cosa non e' stato fatto

Per coerenza con il piano Step 13, non sono stati introdotti:

- database;
- chiamate di rete runtime;
- autenticazione;
- upload file;
- editing configurazioni da UI;
- grafici complessi;
- backtesting;
- research lab;
- stato persistente multi-run avanzato.

## Valutazione

Step 13 e' completato.

La UI e' volutamente minima ma utile: mostra una run completa, usa dati locali importati, rende visibili warning e allocation, e conserva la separazione architetturale impostata dopo il restart.

Il sistema resta ancora file-based e locale. Questo e' coerente con la traiettoria scelta: prima solidita' del dominio e della pipeline, poi superficie applicativa, poi eventualmente persistenza, import piu' ricco o UI di gestione.

## Prossime decisioni possibili

I prossimi incrementi possono andare in una di queste direzioni:

- Step 14 - manifest e storico run locali: indicizzare le run generate, mostrare lista e dettaglio run.
- Step 14 - hardening della UI: aggiungere test Web smoke e gestione errori piu' granulare.
- Step 14 - data/import avanzato: validazione piu' ricca dei file e diagnostica import.
- Step 14 - configuration surface: visualizzare configurazione attiva senza permettere ancora editing.

La prossima azione consigliata e' introdurre un manifest locale delle run, per non restare vincolati alla sola run corrente e preparare una UI realmente consultabile nel tempo senza introdurre un database.
