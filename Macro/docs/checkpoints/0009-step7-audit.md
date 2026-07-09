# Macro Regime - Step 7 Audit

Data: 2026-07-02

## Scopo

Questo audit verifica lo stato di Step 7 prima di introdurre UI o database.
Il controllo riguarda:

- completezza dell'allocation domain;
- coerenza tra Application e Reporting;
- duplicazione delle fixture nei test;
- opportunita' di introdurre adapter Infrastructure demo per policy, portfolio e tilt;
- decisione sul prossimo incremento: data/import o UI minima.

## Verdetto sintetico

Step 7 e' completo come prima vertical slice locale:

- il dominio di allocation contiene i concetti minimi e le regole core;
- Application orchestration resta sottile e dipende da porte;
- Reporting formatta il risultato senza introdurre logica decisionale;
- Infrastructure e' ancora limitata a persistenza/report locali, senza database e senza rete;
- build, test e gate architetturali sono verdi.

Step 7 non e' ancora un motore di portfolio production-grade. Questa e' una scelta corretta per il piano attuale: prima serviva chiudere un nucleo coerente, testabile e verticale.

La prossima mossa consigliata non e' la UI. Prima conviene introdurre adapter Infrastructure demo deterministici e poi affrontare data/import.

## 1. Completezza allocation domain

Implementazione presente:

- `AllocationWeight`;
- `AssetClass`;
- `AllocationBand`;
- `PortfolioWeight`;
- `CurrentPortfolio`;
- `StrategicAllocationPolicy`;
- `RegimeTiltRule`;
- `DecisionSuggestion`;
- `AllocationProposalLine`;
- `AllocationProposal`;
- `AllocationProposalService`.

Regole coperte:

- pesi validi nel range 0..1;
- policy con bande uniche, strategici normalizzati e coerenti con min/max;
- portafoglio corrente con asset class uniche e pesi normalizzati;
- proposal con as-of date valida, righe presenti, target normalizzati e costo non negativo;
- sospensione dei tilt in `UncertainTransition`;
- applicazione di tilt per regime confermato;
- clipping dei target entro banda;
- cap di turnover;
- blocco con `ManualReviewRequired` quando il costo stimato supera il massimo policy;
- suggerimenti decisionali base: hold, wait, partial rebalance, full rebalance, manual review.

Copertura test rilevante:

- `AllocationWeight` rifiuta valori fuori range;
- `AllocationBand` rifiuta strategici fuori banda;
- `StrategicAllocationPolicy` rifiuta pesi non normalizzati;
- `CurrentPortfolio` rifiuta duplicati e pesi non normalizzati;
- `AllocationProposalService` rispetta bande, turnover cap, cost cap e regime incerto.

Gap intenzionali o da chiudere prima dell'uso reale:

- manca una validazione esplicita della compatibilita' tra asset class del portafoglio corrente e asset class della policy;
- non c'e' ancora un modello per costi per asset class, liquidita', tasse o vincoli non lineari;
- la proposal non conserva ancora un identificativo/versione della policy usata;
- non c'e' confronto con una proposal precedente;
- non c'e' schema persistito specifico per allocation proposal.

Decisione: allocation domain e' sufficiente per Step 7, ma prima di collegarlo a dati reali o UI va aggiunta almeno la validazione di compatibilita' portfolio-policy.

## 2. Coerenza Application e Reporting

Application e' coerente con l'architettura:

- `GenerateAllocationProposalUseCase` orchestra provider e servizio di dominio;
- `RunRegimeAnalysisUseCase` compone calcolo regime, allocation proposal e report;
- le dipendenze esterne passano da porte;
- gli errori applicativi restano espliciti e non lanciano eccezioni infrastrutturali;
- Domain non conosce Application, Reporting o Infrastructure.

Reporting e' coerente:

- `RegimeReportContent` lega snapshot e allocation proposal e valida la coerenza dell'as-of date;
- `GenerateRegimeReportUseCase` delega rendering e salvataggio;
- `MarkdownRegimeReportRenderer` formatta sezioni regime, probabilita', feature, spiegazioni e allocation proposal;
- il renderer non decide rebalance, non normalizza pesi e non applica tilt.

Rischi da monitorare:

- `RunRegimeAnalysisUseCase` non deve diventare un contenitore di logica di dominio;
- il report markdown usa ancora formattazione semplice e non ha viste comparative;
- se la proposal verra' persistita, il report dovra' includere policy id/version e input provenance.

Decisione: Application/Reporting sono coerenti con lo stato del piano.

## 3. Duplicazione fixture

La duplicazione esiste ed e' visibile in piu' aree:

- fixture allocation in `MacroRegime.Application.Tests`;
- fixture simili nei test `Analysis`;
- fixture replicate negli end-to-end di `MacroRegime.Infrastructure.Tests`;
- snapshot/proposal create di nuovo nei test `MacroRegime.Reporting.Tests`;
- model version e feature set version ripetuti in piu' test.

Per ora non e' un blocco architetturale, perche' i test restano leggibili e isolati. Sta pero' diventando debito reale: aggiungere data/import o UI sopra fixture duplicate aumenterebbe la probabilita' di divergenze tra scenari.

Decisione: prima o durante il prossimo incremento conviene introdurre piccoli builder di test, senza creare ancora un progetto shared pesante. Opzione consigliata:

- `RegimeSnapshotTestBuilder`;
- `AllocationPolicyTestBuilder`;
- `CurrentPortfolioTestBuilder`;
- `AllocationProposalTestBuilder`;
- `DemoInputTestBuilder` per data snapshot, model version e feature set version.

Questi builder possono vivere nei singoli progetti test, oppure in un piccolo progetto `MacroRegime.Testing` solo se la duplicazione continua a crescere.

## 4. Adapter Infrastructure demo

Decisione: si', conviene introdurli prima della UI.

Motivo: oggi la vertical slice funziona nei test, ma fuori dai test mancano provider concreti per alimentare i casi d'uso. Una UI minima ora rischierebbe di hardcodare dati nel layer sbagliato o duplicare fixture di test.

Adapter consigliati:

- `DemoStrategicAllocationPolicyProvider`;
- `DemoCurrentPortfolioProvider`;
- `DemoRegimeTiltRuleProvider`.

Per rendere davvero eseguibile `RunRegimeAnalysisUseCase` fuori dai test, conviene includere nello stesso incremento anche provider demo deterministici per:

- `IDataSnapshotProvider`;
- `IModelVersionProvider`;
- `IFeatureSetProvider`.

Vincoli:

- nessun database;
- nessuna rete;
- nessun EF;
- nessun clock implicito;
- output deterministici;
- test Infrastructure dedicati.

## 5. Data/import o UI minima

La UI minima non e' il prossimo passo migliore.

Ordine consigliato:

1. introdurre adapter Infrastructure demo deterministici per tutti i provider necessari alla vertical slice;
2. ridurre la duplicazione fixture piu' critica con builder di test;
3. introdurre data/import locale, inizialmente file-based e senza database;
4. solo dopo aggiungere una UI minima che consumi use case gia' eseguibili.

Questo mantiene la direzione del piano: prima dominio e applicazione solidi, poi input reali o dimostrativi, infine interfaccia.

## Verifiche eseguite

Comandi eseguiti:

```powershell
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore
rg -n "EntityFramework|AspNetCore|DbContext|DbSet|HttpClient|Sqlite|SqlConnection|DateTime\.Now|DateTimeOffset\.Now" src\MacroRegime.Domain src\MacroRegime.Application --glob '!**/bin/**' --glob '!**/obj/**'
rg -n "MacroRegime.Infrastructure|MacroRegime.Reporting|File\.|Directory\.|Path\." src\MacroRegime.Domain src\MacroRegime.Application --glob '!**/bin/**' --glob '!**/obj/**'
rg -n "ProjectReference Include=.*MacroRegime.Infrastructure|ProjectReference Include=.*MacroRegime.Reporting" src\MacroRegime.Domain src\MacroRegime.Application tests\MacroRegime.Domain.Tests tests\MacroRegime.Application.Tests --glob '*.csproj'
rg -n "HttpClient|WebRequest|Sqlite|SqlConnection|DbContext|DbSet|EntityFramework" src tests --glob '!**/bin/**' --glob '!**/obj/**'
rg -n "CreatePolicy|CreatePortfolio|CreateTiltRules|CreateAllocationProposal|CreateGoldilocksDataSnapshot|CreateFeatureSetVersion|CreateModelVersion|CreateSnapshot" tests --glob '!**/bin/**' --glob '!**/obj/**'
```

Risultati:

- build: superata, 0 warning, 0 errori;
- test: superati 103/103;
- gate Domain/Application: nessuna violazione trovata;
- gate riferimenti progetto: nessuna dipendenza vietata trovata;
- gate rete/database: nessun uso di HTTP, EF o SQL trovato;
- duplicazione fixture: presente e da ridurre nel prossimo incremento.

## Decisione finale

Step 7 e' chiuso correttamente come vertical slice locale.

Non aggiungiamo UI o database adesso.

Il prossimo incremento deve essere:

- adapter Infrastructure demo deterministici per provider regime e allocation;
- test Infrastructure sui provider demo;
- piccola pulizia fixture per evitare divergenze;
- poi data/import locale.

La UI minima arriva dopo, quando esiste una pipeline applicativa eseguibile senza fixture di test e senza logica hardcoded nel front-end.
