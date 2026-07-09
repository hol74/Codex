# Post-mortem del primo tentativo Macro-Regime

Data: 2026-07-02

## Scopo

Questo documento valuta il primo tentativo di implementazione del Macro-Regime Engine presente nel repository Finance, in particolare nei cinque progetti sotto:

- `C:\ProgettiAzure\Codex\Finance\src\Finance.Domain`
- `C:\ProgettiAzure\Codex\Finance\src\Finance.Application`
- `C:\ProgettiAzure\Codex\Finance\src\Finance.Infrastructure`
- `C:\ProgettiAzure\Codex\Finance\src\Finance.Analytics`
- `C:\ProgettiAzure\Codex\Finance\src\Finance.Web`

L'obiettivo non e' giudicare se il codice "funziona", ma se la sua architettura e' adeguata al progetto Macro-Regime definito nei documenti:

- `macro_regime.md`
- `macro_regime_github.md`
- `macro_regime_plan.md`
- `macro_regime_governance.md`
- `macro_regime_delivery_plan.md`

## Esito sintetico

Il primo tentativo e' tecnicamente utile ma architetturalmente non soddisfacente.

Non e' un fallimento da buttare: contiene concetti giusti, seed demo, entita' EF, dashboard, snapshot as-of e test verdi. Tuttavia non rispetta il principio piu' importante della nuova governance: il cuore del Macro-Regime Engine deve essere un domain/application core puro, testabile senza database, UI, EF Core, API esterne o file system.

La decisione consigliata e':

> restart architetturale con recupero selettivo del prototipo come reference implementation.

## Evidenze raccolte

### Struttura del tentativo

Il codice Finance e' organizzato in cinque progetti:

- `Finance.Domain`
- `Finance.Application`
- `Finance.Infrastructure`
- `Finance.Analytics`
- `Finance.Web`

La struttura nominale e' buona e assomiglia alla separazione desiderata. Il problema e' che le responsabilita' effettive non sono distribuite nel modo corretto.

### Stato dei test

E' stato eseguito:

```text
dotnet test C:\ProgettiAzure\Codex\Finance\Finance.slnx --no-restore
```

Esito:

- test totali: 6
- passati: 6
- falliti: 0

Questo indica che il prototipo e' coerente internamente e compilabile. Il problema non e' un codice rotto, ma un'impostazione non adatta a diventare il nucleo governato del nuovo sistema.

## Cosa funziona

### 1. Il dominio informativo e' stato gia' individuato

Il tentativo contiene gia' molte entita' coerenti con la letteratura e con il piano:

- `MacroDataSource`
- `MacroSeries`
- `DataVintage`
- `MacroObservation`
- `MarketSeries`
- `MarketObservation`
- `MacroFeatureSetVersion`
- `MacroFeatureDefinition`
- `MacroFeatureValue`
- `RegimeModel`
- `RegimeModelVersion`
- `RegimeRun`
- `RegimeProbability`
- `RegimeExplanation`
- `RegimeReport`
- `AllocationProposal`
- `RebalanceRecommendation`

Questa tassonomia e' utile e va recuperata come vocabolario di partenza.

### 2. Il concetto as-of e vintage-aware e' presente

Il prototipo include:

- data osservazione;
- data pubblicazione;
- vintage;
- snapshot as-of;
- test sul fatto che una revisione futura non venga usata prima della sua disponibilita'.

Questo e' uno dei requisiti piu' importanti del progetto, perche' riduce il rischio di look-ahead bias.

### 3. La baseline rule-based esiste

Il prototipo implementa una baseline con dimensioni:

- Growth;
- Inflation;
- Risk;
- Monetary;
- Credit.

Include score normalizzati, probabilita' di regime e stato `UncertainTransition` quando la confidence e' sotto soglia.

### 4. La dashboard e' gia' dimostrativa

La UI MVC mostra:

- regime primario;
- composite score;
- confidence;
- probabilita' dei regimi;
- feature correnti;
- driver;
- segnali contrari;
- dati macro e market proxy;
- calendario rilasci.

Questa dashboard e' utile come reference per la futura UI, ma non deve guidare la nuova architettura.

### 5. Esiste un seed demo ricco

Il seeder crea:

- portafoglio demo;
- asset class;
- policy di allocazione;
- serie macro;
- serie mercato;
- feature;
- regime run;
- report regime-aware;
- proposta allocativa demo.

Questo e' prezioso per costruire fixture e scenari sintetici del nuovo sistema.

## Cosa non funziona

### 1. Il cuore del calcolo e' in Infrastructure

Il problema principale e' che il servizio `RegimeCalculationService` vive in `Finance.Infrastructure` e dipende direttamente da:

- `FinanceDbContext`;
- `IMacroDataFoundationService`;
- EF Core;
- persistenza dei run;
- creazione implicita di model version e feature definition.

Questo viola la regola della nuova governance:

> Il dominio C# deve restare testabile senza database, UI, API esterne o file system.

### 2. Troppe responsabilita' nello stesso servizio

Il servizio di calcolo fa troppe cose:

- recupera snapshot;
- crea model version se mancante;
- crea feature definitions se mancanti;
- calcola feature;
- calcola composite score;
- calcola probabilita';
- decide regime primario;
- salva feature values;
- salva run;
- salva probabilities;
- salva explanations;
- salva report;
- scrive audit event.

Questa concentrazione rende difficile testare, versionare, spiegare e sostituire componenti.

### 3. Il dominio e' modellato come entita' EF, non come domain core

Le entita' del dominio sono principalmente classi mutabili con proprieta' pubbliche e navigation properties. Questo e' accettabile per persistenza, ma non basta per rappresentare invarianti di dominio.

Mancano o sono deboli:

- value object per probabilita';
- value object per date as-of/pubblicazione/disponibilita';
- validazione di somme probabilistiche;
- policy immutabile;
- result object per errori di dominio;
- separazione fra input calcolabile e output persistibile.

### 4. Le formule sono hardcoded dentro il servizio

Le formule per Growth, Inflation, Risk, Monetary e Credit sono dentro il codice infrastrutturale.

Questo rende difficile:

- versionare formule;
- testare singole formule;
- confrontare formula v0.1 e v0.2;
- produrre model card precisa;
- promuovere o ritirare un modello.

### 5. Il seed e' troppo centrale

Il seed contiene molte decisioni di dominio. Questo e' utile per demo, ma rischia di diventare la fonte implicita della verita'.

Nel nuovo sistema il seed deve diventare:

- fixture;
- scenario demo;
- input di test;
- non luogo primario della logica.

### 6. Application layer troppo sottile

`Finance.Application` espone interfacce e read model, ma molta logica vive altrove. Il layer applicativo non orchestra ancora use case puri e non protegge il dominio dall'infrastruttura.

### 7. Analytics e' quasi vuoto

`Finance.Analytics` contiene solo una funzione elementare `Weight`. Non rappresenta ancora un vero motore di analytics o portfolio math.

### 8. Mancano test di dominio sul motore

I test esistenti sono utili, ma per Macro-Regime sono soprattutto integration test su SQLite in memoria.

Mancano test puri su:

- normalizzazione feature;
- mapping feature -> probabilita';
- soglia `UncertainTransition`;
- divergenza fra segnali;
- somma probabilita';
- driver e segnali contrari;
- vincoli allocativi.

## Cosa recuperare

### Recuperare come vocabolario

- nomi delle entita' macro;
- categorie Growth, Inflation, Risk, Monetary, Credit;
- regimi estesi: Goldilocks, Reflation, LateCycleOverheating, Stagflation, DeflationBust;
- concetto di `UncertainTransition`;
- concetto di `RegimeRun`;
- concetto di `RegimeProbability`;
- concetto di `RegimeExplanation`.

### Recuperare come fixture

- serie seed: ISM PMI, Sahm Rule, breakeven, HY OAS, curva 10Y-2Y, VIX;
- market proxy: EURUSD, GLD, VWCE proxy, IEF proxy, JNK/LQD;
- feature baseline v0.1;
- run demo;
- report demo;
- policy allocativa demo.

### Recuperare come test case

- test vintage/as-of;
- test idempotenza del calcolo per stessa data;
- test creazione di probabilities ed explanations;
- test su assenza dati;
- test su dimensioni mancanti.

### Recuperare come UI reference

- layout della dashboard;
- sezioni "Probabilita' regime";
- "Feature correnti";
- "Driver e segnali contrari";
- "Proxy mercato";
- "Calendario rilasci".

## Cosa scartare o non portare nel nuovo core

### Da non portare nel dominio

- dipendenza da `FinanceDbContext`;
- navigation properties EF;
- `DbSet`;
- `Include`;
- `SaveChangesAsync`;
- generazione automatica di model version dentro il calcolo;
- persistenza dentro il detector;
- report creation dentro il detector.

### Da non portare come architettura

- servizio unico che calcola e persiste;
- formule hardcoded in Infrastructure;
- seed come fonte della logica;
- UI prima del domain core;
- test del motore solo via SQLite.

## Decisione architetturale

Il primo tentativo non va proseguito con refactor incrementale diretto.

La decisione e':

> creare un nuovo sistema Macro-Regime con restart architetturale, usando il tentativo Finance come reference implementation e sorgente di fixture, ma non come base da estendere direttamente.

## Motivazione della decisione

Un refactor incrementale dentro Finance rischierebbe di:

- preservare accoppiamenti indesiderati;
- far dipendere il nuovo dominio da EF;
- far partire la UI troppo presto;
- rendere difficile testare il baseline model in modo puro;
- confondere portafoglio personale esistente e motore Macro-Regime;
- ritardare la definizione di contratti puliti.

Un restart architetturale consente invece di:

- costruire il dominio nel posto giusto;
- isolare il calcolo baseline;
- usare test puri come guardrail;
- reintrodurre Infrastructure solo quando il core e' stabile;
- recuperare il prototipo senza ereditarne i difetti.

## Criteri di successo del restart

Il restart sara' considerato corretto quando:

- il nuovo `MacroRegime.Domain` non dipende da EF Core;
- il baseline detector gira completamente in memoria;
- esistono test puri su feature, probabilita' e `UncertainTransition`;
- la persistenza e' un adapter, non parte del calcolo;
- lo snapshot as-of e' un input del caso d'uso, non una query interna al detector;
- i concetti recuperati da Finance sono mappati esplicitamente nel nuovo dominio;
- la UI non viene ricostruita prima del core.

## Rischi residui

| Rischio | Mitigazione |
|---|---|
| Perdere lavoro utile del prototipo | Creare una matrice di mapping prototype -> nuovo sistema |
| Ripetere lo stesso accoppiamento | Bloccare ogni dipendenza EF nel Domain |
| Sovra-progettare prima dei test | Milestone 1 limitata a domain core e baseline |
| Rimandare troppo la persistenza | Definire porte application fin dall'inizio |
| Confondere restart con riscrittura totale | Recuperare fixture, naming, UI reference e test case |

## Prossima azione

Prima di creare lo scheletro C# occorre scrivere e approvare il piano di restart architetturale:

- `macro_regime_architectural_restart_plan.md`

Solo dopo quel piano si potra' creare la nuova solution o riorganizzare quella esistente.
