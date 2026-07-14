# Protocollo di valutazione - Fase E

Data: 2026-07-13

## Obiettivo

Confrontare la baseline rule-based con modelli challenger senza look-ahead bias,
senza contaminare il runtime C# e senza promuovere automaticamente alcun modello.

## Dataset gate

L'input autorevole e' il file `historical-dataset-*.json` prodotto dalla Fase D.
Ogni esperimento registra almeno:

- SHA-256 e dimensione del file;
- versione dello schema;
- intervallo dichiarato e intervallo effettivamente osservato;
- numero di righe, date mancanti, simboli e orizzonti forward return;
- esito dei controlli point-in-time.

I sample locali servono solo ai test. Nessun risultato ottenuto sui sample puo'
essere usato per un Model Gate.

## Controlli anti-leakage

- `publicationDate` e `availabilityDate`/`vintageDate` macro non possono superare `asOfDate`.
- La data iniziale di ogni forward return coincide con `asOfDate`.
- La data finale non precede `asOfDate + horizonDays`.
- Train e test non si sovrappongono.
- Trasformazioni, scaling e selezione iperparametri vengono adattati solo sul train.
- Il test viene usato una sola volta per la valutazione out-of-sample del fold.

## Walk-forward

Configurazione baseline obbligatoria:

- finestra train rolling: 10 anni;
- finestra test: 2 anni;
- avanzamento: 1 anno;
- prima finestra ancorata alla prima data osservata;
- nessuna ottimizzazione sul test.

Un dataset con meno di 12 anni non produce fold validi. Il corpus reale Slice E2
copre 2008-04-30 / 2025-12-31 e produce 6 fold completi; questo supera il gate di
copertura, ma non equivale ancora al superamento del Model Gate.

## Politica del corpus reale Slice E2

- macro revisionabili mensili: initial release ALFRED;
- `INDPRO_YOY`: calcolato dai livelli `INDPRO` di prima pubblicazione;
- `SAHM`: ricostruito dalle prime pubblicazioni `UNRATE`, con fallback sulle
  initial release `SAHMREALTIME` per i buchi non ricostruibili;
- una serie mensile con oltre tre mesi di ritardo rispetto all'as-of viene
  rifiutata dal popolatore;
- serie finanziarie giornaliere FRED: storia corrente, non vintage;
- `HY_OAS`: rappresentato dal proxy long-history `BAA10Y`, marcato nei record
  come `FRED:BAA10Y`, poiche' `BAMLH0A0HYM2` e' limitato a tre anni da aprile 2026;
- prezzi market: Yahoo Finance adjusted close, con fallback al close;
- campionamento: ultimo giorno di mercato completo del mese.

Queste differenze di qualita' point-in-time devono comparire in ogni report di
valutazione: le serie giornaliere correnti possono incorporare correzioni storiche
e il proxy Baa non e' semanticamente identico a un high-yield OAS.

## Metriche previste

Le slice successive aggiungeranno:

- confronto con recessioni NBER e cronologia crisi curata;
- asset alignment a 28, 56 e 91 giorni;
- tilt simulation contro allocazione strategica;
- penalita' asimmetrica per falsi negativi in Stagflation e Deflation/Bust;
- stabilita' dei regimi e frequenza delle transizioni.

Accuracy isolata non e' sufficiente per la promozione.

## Baseline misurata nella Slice E3

La baseline viene eseguita dal codice C# autorevole; il lab Python non ne replica
le regole. Il report walk-forward registra per fold e sull'unione delle date test:

- confidenza media e mediana;
- quota sotto la soglia di conferma e quota `UncertainTransition`;
- tasso di transizione del regime operativo;
- distribuzione primary/operational;
- rendimenti forward descrittivi per asset, orizzonte e regime operativo.

I test biennali avanzano di un anno e quindi si sovrappongono. Le metriche per
fold conservano questa struttura; l'aggregato usa ogni data test una sola volta.
I rendimenti condizionati non sono una strategia di trading ne' un promotion
score. Non si calcola regime accuracy senza una ground truth esterna versionata.

La versione corrente `0.1-demo` e' efficace dal 2026-07-01: l'applicazione al
2008-2025 e' un benchmark retrospettivo, non una pretesa di performance live o
di disponibilita' storica del modello.

## Ground truth recessiva NBER

La ground truth binaria US e' versionata in
`ground-truth/nber-us-recessions-v1.json`. La regola mensile segue la convenzione
NBER/FRED USREC: il peak month e' ancora espansione; sono recessivi i mesi dal
successivo al picco fino al trough incluso.

Il mapping della baseline e' fissato prima della lettura dei risultati:

- primary signal: `primaryRegime == DeflationBust`;
- operational signal: `operationalRegime == DeflationBust`;
- `UncertainTransition` non e' contato come recessione confermata, ma viene
  misurato separatamente durante i mesi recessivi.

Il report conserva confusion matrix, recall, false-negative rate, specificity,
false-positive rate, precision, accuracy, balanced accuracy, F1, date di errore
e detection lag per episodio. Metriche con denominatore zero restano `null`.

La cronologia NBER e' ex-post: puo' essere annunciata con ritardo e serve solo
come label di valutazione. Non copre inflazione/stagflazione, stress finanziario
fuori recessione o l'intera tassonomia multi-regime. Con sole due osservazioni
recessive nelle date OOS uniche, le metriche sono fragili e l'accuracy e' molto
influenzata dallo sbilanciamento di classe.

## Cronologia multi-label degli stress non recessivi

La cronologia `ground-truth/us-non-recession-stress-v1.json` copre dimensioni
che la label NBER binaria non rappresenta: stress finanziario, growth scare,
shock inflazionistico e tightening monetario. Le label possono sovrapporsi; gli
episodi non possono invece sovrapporsi a un mese recessivo NBER e il comando
`stress-report` verifica automaticamente questo vincolo.

Le associazioni label-regime sono ipotesi semantiche congelate prima del primo
report. Il risultato misura soltanto date positive, distribuzioni, quota di
regimi attesi e `UncertainTransition`. Non vengono calcolate accuracy o
specificity: la cronologia e' curata e non esaustiva, quindi i mesi non
etichettati non sono veri negativi affidabili.

Il primo report v1.4 e' negativo: sugli stress OOS, financial stress e growth
scare hanno allineamento 0%; inflation shock e monetary tightening circa 4-5%.
La v1.4 non viene modificata sullo stesso campione. Il risultato evidenzia sia un
blind spot di stress finanziario sia il limite di mappare una singola dimensione
su un regime composito senza condizionare sulle altre dimensioni.

## Challenger clustering v1

Il primo challenger usa k-means deterministico sulle cinque feature normalizzate.
Per ogni fold:

1. scaler e centroidi sono adattati solo sul train;
2. il cluster recessivo è scelto solo tra cluster con almeno un mese NBER train;
3. prevalenza Laplace-smoothed e tie-break sono deterministici;
4. le predizioni test vengono congelate prima del calcolo delle metriche;
5. nessun numero di cluster o altra configurazione viene selezionato sul test.

Poiché i test biennali si sovrappongono, il report mostra sia le 144 osservazioni-
fold sia 84 date uniche; per queste ultime usa la prima predizione fold eleggibile,
policy fissata nella configurazione.

Il risultato negativo viene conservato con model card. L'accuracy non può
compensare recall nullo sulla classe recessiva; nessuna promozione è automatica.

## Challenger previsti

Ordine iniziale: HMM, clustering, Markov switching, jump model. Dopo l'esito di
E5, questo ordine e' sospeso fino alla chiusura di E6: un modello temporale non
deve apprendere e rendere persistenti feature gia' sature o semanticamente
ambigue. Ogni challenger
deve avere configurazione versionata, risultati out-of-sample e model card. I
risultati negativi vengono conservati.

## Gate E6 - Feature e baseline

Prima di creare un nuovo challenger sono obbligatori:

1. audit riproducibile delle distribuzioni normalizzate sull'intero storico e
   sulle date OOS uniche;
2. soglie versionate per saturazione ai bordi, concentrazione del regime
   dominante, numero minimo di regimi primari osservati e quota di
   `UncertainTransition`;
3. test di raggiungibilita' su scenari archetipici per tutti i regimi primari;
4. nuova versione esplicita di feature set e baseline per ogni modifica alle
   formule; nessuna riscrittura retroattiva della `0.1-demo`;
5. riesecuzione degli stessi report E3-E5 per misurare miglioramenti e
   regressioni senza selezionare formule sui mesi test;
6. nessuna dichiarazione di efficacia multiregime basata sulla sola ground truth
   NBER, che misura esclusivamente recessione/non recessione.

La configurazione `models/baseline-audit-v1.json` e' diagnostica: il fallimento
del gate non blocca la scrittura del report, ma blocca HMM e promozione. Le
soglie potranno cambiare solo in una nuova configurazione motivata e versionata.

### Candidate baseline v1

La prima candidate E6 modifica soltanto le normalizzazioni, mantenendo formula
dei raw regime score e confirmation threshold della demo:

- `CREDIT_STRESS`: mapping inverso del proxy `BAA10Y` fra 1% e 4%;
- `MONETARY_COND`: mapping non monotono centrato su curva 10Y-2Y a +0,5%, con
  penalita' per inversione e steepening estremo;
- `INFL_PRESS`: mapping T10YIE fra 1,5% e 3,0%, con limite esplicito che il
  breakeven non sostituisce inflazione realizzata e momentum.

La candidate e' una nuova versione e non riscrive la `0.1-demo`. Dopo la prima
valutazione non si abbassa la confirmation threshold sullo stesso benchmark; un
eventuale redesign successivo richiede nuova versione e configurazione fissata
prima della valutazione.

### Candidate baseline v1.1

La v1.1 aggiunge dati temporali senza modificare raw score o soglia:

- CPI YoY ricavato da livelli CPIAUCSL di prima pubblicazione;
- momentum CPI e variazione curva calcolati fra il valore disponibile al cutoff
  corrente e quello disponibile tre mesi prima;
- nessuna osservazione pubblicata dopo uno dei due cutoff puo' entrare nel delta;
- corpus e dataset sono separati dagli artefatti delle candidate precedenti.

La v1.1 viene valutata una sola volta sulla configurazione dichiarata. Il gate
residuo su confidence/raw score non puo' essere corretto abbassando la soglia
dopo la lettura dell'OOS: richiede una nuova versione train-only e un futuro
holdout/shadow-live.

### Candidate baseline v1.2 e preflight train-only

La configurazione v1.2 viene congelata prima dell'evaluation e lega archetipi,
pesi confidence e hash del dataset. `baseline-train-gate` usa esclusivamente la
coda biennale di ciascun outer train per i diagnostici; l'outer test non entra in
alcun gate. Solo il superamento del minimo di fold eleggibili autorizza i report
OOS.

Il primo preflight v1.2 ha prodotto 0 fold eleggibili su 6. La configurazione non
viene corretta post-hoc e l'OOS non viene aperto. Prima di una nuova candidate va
versionato un gate v2 che separi integrita' e copertura aggregate dalla robustezza
per-fold, evitando di imporre diversita' multiregime a ogni breve biennio.

### Train gate v2

Il gate v2 mantiene le soglie v1 ma assegna ogni controllo alla corretta unita'
di analisi:

- feature integrity: union delle inner-validation, date deduplicate;
- regime coverage: la stessa union, per misurare copertura lungo piu' cicli;
- operational robustness: `UncertainTransition` su ciascun fold, con quorum
  preregistrato.

Ogni fold esclude il proprio test. Poiche' le finestre rolling avanzano di un
anno, date gia' test per un fold possono diventare train di un fold successivo:
il gate e' adatto allo sviluppo temporale ma non crea un holdout finale vergine.

Il gate v2 reale passa copertura e robustezza operativa ma fallisce integrita'
per la saturazione aggregata di `RISK_APPETITE` (27,38% contro 25%). Non si
modifica la soglia; una correzione VIX richiede nuova versione del modello.

### Candidate baseline v1.3

La v1.3 sostituisce soltanto il mapping VIX con una logistica inversa centrata a
20 e scala 7. La configurazione viene congelata prima dell'evaluation; l'hash
dell'evaluation viene poi legato al gate v2 prima di aprire il report train-only.

Il mapping elimina la saturazione `RISK_APPETITE` (1,19%), ma il gate operativo
scende a 2 fold validi su 6. La candidate e' respinta senza aprire l'OOS. Ogni
successivo riallineamento di archetipi/confidence deve avvenire in una nuova
versione usando solo inner fit/validation.

### Candidate baseline v1.4

La v1.4 riallinea l'intera geometria alla scala VIX logistica senza stimare
coordinate da outcome storici: ogni target risk conserva il livello VIX
semantico della v1.2. Anche il cutoff divergente viene tradotto allo stesso VIX.
La confidence usa fit non potenziato e separazione relativa, mentre le
probabilita' mantengono lo score quadratico.

Il train gate v2 passa integralmente (6/6 fold operativi). L'OOS viene quindi
aperto una sola volta: audit superato, 4 regimi, incertezza 2,38%. NBER mantiene
recall 100% ma precision 20% e F1 33,33%, regressione da conservare. La v1.4 e'
baseline di ricerca, non promozione operativa e non holdout finale.

## Model Gate

La promozione richiede revisione umana e almeno:

1. dataset reale pluriennale validato e manifestato;
2. confronto out-of-sample con la baseline;
3. robustezza su piu' fold e periodi di crisi;
4. spiegazione di costi, limiti e failure mode;
5. nessuna regressione dei vincoli IPS e di governance.

Calendario release persistito, indici incrementali per dataset grandi e stress test completi
restano integrazioni pianificate; la loro assenza deve comparire come limite in
ogni report che precede tali implementazioni.

## Gaussian HMM v1

Il primo challenger temporale dopo E6 e' congelato in
`models/gaussian-hmm-recession-v1.json`. In ogni fold:

1. lo standardizzatore e' stimato sul solo train;
2. Baum-Welch stima un HMM gaussiano diagonale a tre stati sul solo train;
3. lo stato recessivo usa prevalenza NBER Laplace-smoothed train-only;
4. il test parte dal posterior train terminale ed e' filtrato in avanti;
5. nessuna osservazione futura o label test entra nella predizione;
6. le date sovrapposte adottano la prima predizione fold eleggibile.

Il gate richiede convergenza in ogni fold e nessuna regressione di recall o F1
rispetto alla baseline operational v1.4. Il report viene scritto anche quando il
gate fallisce, per conservare integralmente i risultati negativi. Qualunque
variante successiva richiede nuovo model id e nuova preregistrazione.

## E8 - Evaluation contracts e shadow ledger

Backtest e shadow-live usano lifecycle diversi. Lo shadow-live e' valido solo se
la predizione viene congelata prima che l'outcome sia disponibile.

Il flusso obbligatorio e':

1. `PredictionLedger` con lifecycle `predicted`, senza label;
2. eventuale `PredictionScore` successivo, che riferisce l'hash del ledger;
3. eventuale `GateDecision`, che riferisce l'hash del report valutato.

Il ledger registra run mode, timestamp, model id/version/role/lifecycle,
forecast origin, information cutoff, probabilita' completa dei regimi,
probabilita' recessiva, decisione derivata, warning, input hash, source
fingerprint e runtime. Gli artefatti sono write-once: un path esistente non puo'
essere sovrascritto.

`dry-run` verifica il contratto ma non costituisce evidenza live. `shadow-live`
puo' essere usato soltanto con una nuova osservazione e un timestamp effettivo.
Il comando di previsione non riceve mai la ground truth. Brier score e log loss
sono calcolati solo nello score separato.

La decisione umana e' persistita con reviewer, rationale e timestamp. Una
decisione `approved` e' vietata se il gate automatico del report e' fallito.

## E9 - Shadow Operations

Ogni nuovo cutoff mensile deve seguire questa catena:

1. i processi C# producono corpus, dataset point-in-time ed evaluation;
2. `ShadowPreflight` congela gli hash degli input e i fingerprint delle
   implementazioni C#/Python;
3. il preflight rifiuta mesi non ancora chiusi, forward return, serie richieste
   mancanti o con oltre tre mesi di lag;
4. `shadow-cycle` crea un solo ledger `shadow-live` per cutoff oppure recupera
   idempotentemente lo stesso file;
5. `ShadowIndex` viene ricostruito dai ledger e non e' fonte autorevole;
6. lo scoring rimane un processo successivo e separato.

Un artefatto storico non puo' essere aggiornato per adeguarlo a una nuova
versione del protocollo. Il preflight retrospettivo del cutoff 2026-06-30 e'
quindi evidenza di audit separata e non fa parte della catena del ledger gia'
congelato. Un retry con hash differenti deve fallire, non produrre una variante
silenziosa.

### E9.2 - Orchestratore e recovery

`shadow-operations` seleziona sempre il mese successivo all'ultimo ledger. Se
quel mese non e' ancora chiuso, emette `no-eligible-month` senza avviare processi
o creare un ciclo; non puo' saltare direttamente a un mese successivo.

La state machine operativa e':

1. `initialized` o `resuming`;
2. population C#;
3. dataset build C#;
4. evaluation v1.4 C#;
5. preflight Python;
6. `prepared` in modalita' `prepare-only`;
7. ledger e indice in modalita' `full`;
8. `ledger-frozen`.

Un exit code non zero produce `failed`, conserva stdout/stderr separati e i
relativi SHA-256. Una retry con lo stesso cutoff e model config valida gli hash
degli artefatti completati e riparte dal primo step incompleto. Un artefatto
completato ma modificato viene rifiutato. Lo stato del ciclo e' atomico,
aggiornabile e non autorevole; ledger, preflight e receipt restano write-once.

Population e' l'unico step che puo' attivare la rete e lo fa tramite la CLI C#
e gli adapter Infrastructure. La chiave FRED non compare mai nel comando o
nello stato. Ne' orchestratore, stato, preflight o ledger ricevono ground truth.
