# ADR 0001: Restart architetturale del Macro-Regime Engine

Data: 2026-07-02

Status: Accepted

## Contesto

Il progetto Macro-Regime deve costruire un sistema informativo per stimare probabilita' di regime macro/market e tradurle in proposte allocative vincolate da policy, rischio, costi, fiscalita' e decisione umana.

Esiste un primo tentativo nel repository `C:\ProgettiAzure\Codex\Finance`. Il tentativo contiene elementi utili:

- entita' macro e market;
- gestione vintage/as-of;
- feature store demo;
- baseline rule-based;
- dashboard MVC;
- seed demo;
- test verdi.

Il post-mortem conclude pero' che il cuore del calcolo vive in `Finance.Infrastructure`, dipende da EF Core e concentra troppe responsabilita' in un servizio monolitico.

## Problema

Il nuovo sistema deve rispettare una regola centrale:

> Il dominio C# deve restare testabile senza database, UI, API esterne o file system.

Il prototipo Finance non rispetta questo vincolo perche':

- il baseline detector dipende da `FinanceDbContext`;
- il detector calcola e persiste nello stesso flusso;
- le formule sono hardcoded in Infrastructure;
- versioni, feature definitions, run e report vengono creati implicitamente;
- i test del motore sono prevalentemente integration test con SQLite.

Continuare con un refactor incrementale dentro Finance rischierebbe di conservare gli accoppiamenti sbagliati.

## Decisione

Avviare un restart architetturale del Macro-Regime Engine.

Il codice Finance resta:

- reference implementation;
- sorgente di fixture;
- fonte di naming e scenari;
- prototipo UI da recuperare dopo il core.

Il nuovo sistema verra' costruito con un core C# puro, separando:

- Domain;
- Application;
- Infrastructure;
- Reporting;
- Web.

La creazione dello scheletro C# avverra' solo dopo:

- ADR minime;
- glossario;
- mapping prototipo;
- domain core design;
- test plan.

## Alternative considerate

### Continuare il refactor dentro Finance

Vantaggi:

- riuso immediato del codice esistente;
- meno file iniziali da creare;
- dashboard gia' disponibile.

Svantaggi:

- alto rischio di mantenere dipendenze EF nel core;
- difficile distinguere vecchio e nuovo;
- UI e persistenza continuerebbero a guidare il design;
- piu' difficile costruire test puri.

Esito: scartata.

### Copiare tutto il prototipo in un nuovo progetto

Vantaggi:

- mantiene quasi tutto il lavoro fatto;
- riduce tempi iniziali apparenti.

Svantaggi:

- copia anche i difetti;
- duplica un monolite logico;
- rende piu' difficile capire cosa e' stato davvero ripensato.

Esito: scartata.

### Restart architetturale con recupero selettivo

Vantaggi:

- consente un domain core pulito;
- recupera naming, fixture e scenari;
- evita dipendenze sbagliate;
- rende test e governance centrali.

Svantaggi:

- richiede piu' documentazione iniziale;
- ritarda la UI;
- richiede mappare con cura cosa recuperare.

Esito: accettata.

## Conseguenze positive

- Il baseline detector sara' testabile in memoria.
- Le formule potranno essere versionate e spiegate.
- La persistenza diventera' un adapter.
- La UI verra' costruita su output applicativi stabili.
- I modelli challenger potranno essere aggiunti senza contaminare il baseline.

## Conseguenze negative

- Lo sviluppo visibile rallenta nelle prime fasi.
- Alcune parti del prototipo andranno riscritte.
- Servira' mantenere una matrice di mapping per non perdere lavoro utile.
- Il progetto avra' piu' documenti prima di avere codice nuovo.

## Vincoli

- `MacroRegime.Domain` non deve dipendere da EF Core.
- `MacroRegime.Domain` non deve dipendere da ASP.NET.
- `MacroRegime.Domain` non deve usare HTTP, file system o database.
- La baseline rule-based viene prima di HMM, clustering e ML.
- `UncertainTransition` resta uno stato operativo obbligatorio.
- Ogni run deve essere ricostruibile as-of date.

## Criteri di accettazione

- Esiste un piano di restart architetturale.
- Esiste una matrice di mapping del prototipo Finance.
- Esiste un test plan prima dello scheletro C#.
- Lo scheletro C# non viene creato prima degli artefatti minimi.
