# Macro Regime - Step 13 Plan

Data: 2026-07-06

## Obiettivo

Costruire una UI minima, sobria e read-only per consultare una run macro-regime locale.

Lo Step 13 non deve introdurre database, rete runtime o modelli avanzati. Deve esporre in modo chiaro il risultato gia' prodotto dalla pipeline Step 12:

- as-of date;
- origine dati;
- modello e feature set;
- regime primario e operativo;
- probabilita' dei regimi;
- feature score;
- driver e segnali contrari;
- warning;
- proposta allocativa.

## Decisione architetturale

Creare un nuovo progetto C#:

- `MacroRegime.Web`.

Tipo consigliato:

- ASP.NET Core Razor Pages o MVC minimale.

Ruolo:

- composition root web locale;
- nessuna logica di dominio nella UI;
- nessun accesso diretto a database;
- nessuna chiamata HTTP esterna;
- lettura/scrittura solo tramite adapter Infrastructure gia' esistenti.

Dipendenze consentite:

- `MacroRegime.Application`;
- `MacroRegime.Domain`;
- `MacroRegime.Infrastructure`;
- `MacroRegime.Reporting`.

Dipendenze non consentite in Domain/Application:

- Web;
- Infrastructure;
- Reporting concreto;
- filesystem;
- database;
- rete.

## Scope funzionale minimo

### 1. Dashboard corrente

Prima pagina della UI:

- data selector o input `as-of date`;
- pulsante/azione per eseguire una run locale;
- stato esecuzione;
- card compatta con regime primario, regime operativo, confidence e composite score;
- badge data source: `Imported`, `Demo`, `DemoFallback`, `EmptyFallback`, `Unspecified`;
- warning visibili, non nascosti.

Nota di design: niente landing page. La dashboard e' la prima schermata.

### 2. Probabilita' regimi

Tabella ordinata:

- rank;
- regime;
- probability;
- evidenza del regime primario.

Opzionale nello stesso step:

- piccola barra orizzontale per probabilita'.

### 3. Feature scores

Tabella compatta:

- code;
- name;
- dimension;
- raw value;
- normalized score;
- weight;
- interpretation.

### 4. Explanations

Lista ordinata:

- driver;
- contrary signals;
- feature code;
- impact.

### 5. Allocation proposal

Tabella:

- asset class;
- current;
- strategic;
- target;
- trade;
- band;
- tilt.

Mostrare anche:

- decision suggestion;
- turnover;
- estimated cost;
- rationale;
- constraints.

### 6. Report markdown

Link o tab secondaria:

- contenuto markdown generato;
- path del report salvato.

Per lo Step 13 e' sufficiente renderizzare testo preformattato o markdown semplice. Non serve editor.

## Input e configurazione

Per evitare una UI troppo ambiziosa, usare inizialmente i sample locali:

- `samples/macro-data-2026-07-01.json`;
- `samples/model-version-baseline.json`;
- `samples/feature-set-baseline.json`;
- `samples/allocation-policy-balanced.json`;
- `samples/current-portfolio-2026-07-01.json`;
- `samples/regime-tilt-rules.json`.

Configurazione minima:

- valori default in `appsettings.json`;
- possibilita' di override via configurazione ASP.NET;
- output locale in `.tmp` o `macro-regime-output-web`.

Non introdurre ancora upload file o gestione configurazioni via UI.

## Piano di delivery

### Step 13a - Web skeleton

- creare `src/MacroRegime.Web`;
- aggiungerlo a `MacroRegime.slnx`;
- configurare layout sobrio;
- aggiungere pagina dashboard vuota ma raggiungibile;
- creare test smoke di progetto se pratico.

Definition of Done:

- build solution verde;
- app avviabile localmente;
- nessuna modifica a Domain/Application.

### Step 13b - Run orchestration web

- comporre gli stessi use case della CLI;
- leggere path configurazione da `appsettings.json`;
- eseguire run per `as-of date`;
- salvare run JSON e report markdown;
- mostrare errori operativi in pagina.

Definition of Done:

- dashboard esegue la pipeline con i sample;
- `Data source: Imported` visibile;
- report salvato su filesystem locale;
- test applicativo o smoke manuale documentato.

### Step 13c - Dashboard result

- mostrare regime summary;
- probabilita';
- feature scores;
- explanations;
- warning.

Definition of Done:

- nessun testo marketing;
- nessun elemento decorativo non informativo;
- layout leggibile su desktop e mobile;
- valori principali scansionabili.

### Step 13d - Allocation panel

- mostrare proposta allocativa;
- rationale;
- constraints;
- turnover e costi.

Definition of Done:

- tabella allocation completa;
- suggestion evidente;
- vincoli e warning non nascosti.

### Step 13e - Verification and checkpoint

- build;
- test;
- smoke UI locale;
- screenshot/verifica visuale se viene avviato browser;
- documento `macro_regime_plan.step13_ui_done.md`.

## Test attesi

Minimo:

- build solution;
- test esistenti invariati;
- test parsing/config web se il progetto lo rende semplice;
- smoke manuale o automatizzato della pagina dashboard.

Test consigliati:

- pagina renderizza una run valida;
- pagina mostra errore se un file strict manca;
- UI mostra `Data source` e warning.

## Non obiettivi

Fuori dallo Step 13:

- autenticazione;
- database;
- upload file;
- editing configurazioni;
- grafici complessi;
- chiamate a provider dati esterni;
- backtesting;
- research lab;
- stato persistente multi-run avanzato.

## Rischi

### Rischio 1 - Duplicare la composition root CLI

Mitigazione:

- accettare duplicazione minima nello Step 13;
- valutare dopo la UI un piccolo factory/composition helper condiviso se la duplicazione diventa reale.

### Rischio 2 - UI troppo demo

Mitigazione:

- usare i file JSON Step 12b come default;
- mostrare chiaramente data source e versioni modello/feature.

### Rischio 3 - Introduzione prematura di stato

Mitigazione:

- output locale file-based;
- niente database;
- una run alla volta nella prima UI.

## Criterio di chiusura Step 13

Step 13 e' chiuso quando:

- `MacroRegime.Web` esiste ed e' nella solution;
- la dashboard locale mostra una run completa prodotta dalla pipeline;
- data source, warning e allocation sono visibili;
- build e test sono verdi;
- lo smoke UI e' documentato;
- non sono state introdotte dipendenze vietate in Domain/Application.
