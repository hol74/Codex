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

## E10 - Model Evidence v2 e dual-timescale

Il gate tecnico della baseline e la promozione operativa sono contratti
distinti. `model-evidence-and-promotion-v2` introduce lifecycle espliciti,
`INSUFFICIENT_EVIDENCE`, Brier score, log loss, average precision, calibrazione,
bootstrap temporale e diagnostica di onset/recovery. Il benchmark 2008-2025 e'
`development-diagnostic-only` e non puo' autorizzare promozione.

Lo stress contract v2 valuta prima quattro dimensioni: growth deterioration,
inflation pressure, financial stress e monetary restriction. Conserva gli
episodi v1 come development e riserva taper shock 2013 e repo stress 2019 a una
partizione `protected-v2`. Anche questa partizione resta storica e diagnostica.

`dual-timescale-regime-v1` separa filtro macro lento e filtro finanziario rapido
senza usare label per fitting o soglie. Il risultato diagnostico e' negativo:
recall e F1 OOS nulli, con falsi segnali persistenti dopo la recessione. Il
modello e' respinto senza tuning post-hoc; ogni variante richiede nuovo id.

Il primo ciclo E9 `full` sul cutoff 2026-07-31 resta temporalmente non
eseguibile fino alla chiusura del mese e alla disponibilita' degli input. Questo
vincolo non e' un fallimento di E10.

## E11 - Preregistrazione del Controlled Candidate Lab

Prima dell'implementazione, E11.1 congela in un manifest immutabile il gate e
le sole tre famiglie ammesse. Il registro contiene hash delle configurazioni,
degli input comuni e del codice che valida la preregistrazione. Un file gia'
esistente non viene mai aggiornato o sostituito.

Le decisioni di feature, parametri e soglia devono avvenire esclusivamente in
inner rolling validation contenuta nell'outer train. I risultati outer OOS
2008-2025, gia' osservati, sono esclusi da selezione e ranking. Dopo il freeze
possono essere aperti soltanto come diagnostica di sviluppo, senza cambiare le
specifiche in risposta all'esito.

I requisiti comuni sono: trasformazioni train-only, inferenza causale,
determinismo, indipendenza dalle label di test, hash della configurazione,
model card e revisione umana. Sono vietati sweep non dichiarati. Il logit puo'
confrontare soltanto le tre soglie preregistrate 0,25, 0,35 e 0,50 nell'inner
validation.

Il superamento del gate inner-only autorizza al massimo `shadow-candidate`.
Nessuna diagnostica storica autorizza `operational-approved`, che resta
subordinato a Evidence v2 prospettica su outcome nuovi.

### E11.2 - Baseline dimensionale v1.5

Per ogni mese la v1.5 calcola le quattro dimensioni E10 e usa soltanto il mese
precedente per derivare gli impulsi positivi di deterioramento della crescita e
stress finanziario. Gli impulsi modificano le tre feature dichiarate; la
geometria, la confidence, la soglia di conferma e la divergence policy v1.4
restano identiche. Il primo mese ha impulso nullo.

La validazione interna usa, per ciascun outer train, una coda lunga quanto il
`testYears` del piano walk-forward. Nessuna riga del corrispondente outer test
entra nel report. Le date duplicate sono aggregate assegnandole al primo fold
eleggibile. Tutte le predizioni vengono congelate prima di associare la ground
truth.

Il runner verifica che gate e configurazione coincidano con gli hash del
manifest E11.1. Il report reale non supera il gate: le metriche binarie sono
invariate, average precision migliora, ma Brier peggiora e nessuna delle due
osservazioni repo-stress protette raggiunge la soglia dimensionale. La candidate
e' quindi `REJECTED_FOR_SHADOW`; il risultato non autorizza tuning o apertura
dell'outer OOS.

### E11.3 - Changepoint-duration e rare-event logit

Il changepoint stima mediana e MAD delle differenze mensili esclusivamente
sull'inner-fit. L'inferenza e' un filtro forward con durata e uscita esplicite.
La probabilita' rende eseguibile la formula preregistrata senza nuovi
parametri: `sigmoid(max(changeScore/2,5, financialStress/0,65) - 1)`. Ne segue
che una soglia dichiarata corrisponde a probabilita' 0,5.

Il logit costruisce cinque livelli e quattro differenze causali, standardizza
sull'inner-fit e usa batch gradient descent deterministico L2. Il peso positivo
e' calcolato solo dalle label di fit e limitato a 10. Un fold senza positivi di
fit e' ineligibile. Le probabilita' validation sono congelate prima delle label;
la label validation puo' selezionare soltanto 0,25, 0,35 o 0,50 secondo F1,
recall, Brier e tie-break gia' dichiarati.

I due report condividono metriche, calibrazione a cinque bin, stress v2 e gate
manifestato. Il changepoint fallisce F1, Brier, ECE, durata dei falsi positivi e
stress protetto. Il logit fallisce recall, F1, average precision e copertura
stress protetta. Entrambi restano respinti.

### E11.4 - Chiusura del gate inner-only

I tre candidati E11 sono stati valutati con zero righe dei rispettivi outer
test: baseline v1.5, changepoint-duration v1 e rare-event-logit v1 sono tutti
`REJECTED_FOR_SHADOW`. L'outer OOS 2008-2025 non viene aperto perche' nessun
modello ha superato il prerequisito inner. Il laboratorio si chiude senza
shadow-candidate e senza modifiche post-hoc.

## E14.7f - Proposta taxonomy post-2005 e review indipendente

La proposta post-2005 e' un artefatto separato: non modifica e non sostituisce
`us-financial-stress-v5.json`. Ogni entry riceve un nuovo `proposalEntryId`; gli
identificatori v5 sono conservati soltanto come riferimenti verificabili.

I due nuovi controlli banking-credit devono essere dossier `reviewed`, mai
auto-accettati. Ogni dossier contiene evidenza affermativa da almeno due gruppi
indipendenti, counterevidence esplicita e digest deterministici. La queue lega
proposta, schema e dossier tramite SHA-256 ed e' write-once.

Soltanto un reviewer diverso dal curatore puo' produrre receipt v2. Receipt
mancanti, hash mismatch, reject o needs-revision lasciano la proposta inattiva.
Questo step non legge osservazioni, dataset, score LOEO o outer OOS e non
autorizza source acquisition, foundation, candidate generation o evaluation.

### E14.7g - Handoff e ingestion receipt

Il generatore del bundle non puo' svolgere la review. Copia byte-identici
proposta, queue e dossier, aggiunge worksheet e template schema v2 con campi
obbligatori volutamente incompleti. Le receipt finite vivono fuori dal bundle.

L'ingestion richiede un hash dossier esatto, un reviewer diverso dal curatore,
una sola receipt per dossier, counterevidence considerata e nessun output
modello usato. Un `accept` richiede inoltre locator aperti, meccanismo e confini
supportati. Qualunque receipt mancante o invalida fallisce chiusa.

Nemmeno due accept attivano automaticamente lo scope: autorizzano soltanto un
gate E14.7h separato. Fino ad allora dati, foundation, candidati, evaluation e
outer OOS restano chiusi.

### E14.7g3/g4 - Revisione mirata e nuova receipt

Una decisione `needs-revision` consente di cambiare soltanto il dossier e
l'hash contestati. I dossier gia' accettati devono restare byte-identici e non
entrano nel bundle mirato. L'autore della revisione deve essere diverso dal
reviewer; la nuova receipt deve legarsi al nuovo hash e riaprire ogni locator.

L'ingestion mirata richiede esattamente una receipt v2 e applica gli stessi
controlli stretti della review iniziale. Un nuovo `accept` non attiva lo scope:
autorizza soltanto E14.7h.

### E14.7h - Attivazione dello scope post-2005

Il gate richiede che ogni dossier corrente sia accettato da receipt
indipendente e propaga nella taxonomy il dossier revisionato e il suo nuovo
confine. Materializza `us-financial-stress-post2005-v1` senza modificare la
taxonomy legacy v5 e senza leggere osservazioni o outer OOS.

L'attivazione accetta lo scope e le label, ma mantiene chiuse acquisizione,
feature foundation, candidati, fitting ed evaluation. Il solo passo successivo
ammesso e' la preregistrazione separata di un manifest di acquisizione fonti.

### E14.7i - Manifest di acquisizione fonti

Il manifest congela prima di ogni accesso di rete: identita' delle fonti,
locator provider-primary, finestra 2006-2025, frequenze, serie o tabelle,
semantica event-time/as-of, regimi metodologici, percorsi raw e policy di
integrita'. Ogni fonte deve essere gia' metadata-ready e deve risolvere in una
delle quattro famiglie preregistrate.

La materializzazione del manifest effettua zero richieste, scrive zero raw
artifact e acquisisce zero osservazioni. Hash mismatch, fonte non pronta,
percorso duplicato o autorizzazione di rete anticipata falliscono chiusi.
L'esecuzione richiede un gate successivo legato all'hash esatto; feature,
candidati, evaluation e outer OOS restano vietati.

### E14.7j - Gate di esecuzione acquisizione

Il gate verifica l'hash esatto del manifest, la chiave FRED richiesta e un
endpoint metadata per ciascuna delle sette fonti. I segreti sono letti soltanto
dall'ambiente e non possono entrare nell'audit. Sono ammessi esclusivamente
HTTPS e redirect verso gli host provider-primary congelati.

Tutti i probe devono restituire HTTP 200 e il marker atteso; credenziale
mancante, errore provider o redirect fuori allowlist bloccano l'intera
acquisizione. Il gate non scarica osservazioni e non scrive raw artifact. Un
esito positivo autorizza soltanto l'acquisizione atomica dei bytes originali e
dei metadati release/vintage; ogni trasformazione rimane vietata.

### E14.7k - Acquisizione raw atomica

Ogni richiesta scrive in una directory staging sorella dello snapshot. I
payload devono rispettare maximum bytes, host allowlist, marker o magic bytes,
finestra e metadati realtime. Al primo errore lo staging viene eliminato; lo
snapshot diventa visibile soltanto con un singolo rename dopo che tutti gli
artifact hanno ricevuto SHA-256.

Le API FRED initial-release sono suddivise in tranche real-time da meno di
2.000 vintage dates e i payload originali restano separati. Il parser in questo
step puo' leggere soltanto struttura, date e metadati necessari alla validazione;
non calcola feature.

I bulk provider che possono contenere revisioni sono marcati `raw-only`.
L'acquisizione completa non costituisce quindi automaticamente vintage fitness:
un audit separato per famiglia deve controllare completezza, metodologia ed
event-time prima di aprire la trasformazione.

### E14.7l - Audit completezza e vintage fitness

L'audit lega per SHA-256 contratto, indice, acquisition audit, scope plan,
fitness plan e schema. Ogni raw artifact viene riletto e confrontato con hash e
dimensione congelati. Per FRED sono obbligatori riconciliazione esatta di
conteggio ed estremi per tranche, date uniche, tranche realtime contigue,
cronologia observation-date/release-date, lag massimo preregistrato e almeno 60
mesi di lookback prima di ogni episodio applicabile. I container SDMX/XLSX devono superare nuovamente l'integrity
test.

Un payload `raw-only` non puo' provare event-time fitness. Sullo snapshot v1
passano `broad-market-repricing` e `funding-liquidity`; falliscono
`banking-credit` e `cross-border-growth` per assenza di release-level vintages,
con l'ulteriore termine FDIC al 2011Q4. Il gate globale richiede quattro famiglie
su quattro: nessuna feature viene trasformata, nessun candidato viene generato
e outer OOS resta chiuso. Il solo passo ammesso e' acquisire artifact datati di
release per H.8/H.10 e FDIC e ripetere lo stesso audit.

### E14.7m - Remediation mirata e blocco strutturale

La remediation legge soltanto calendari e locator provider-primary e resta
legata agli hash E14.7l. H.8 presenta tutti gli 88 mesi di release richiesti tra
gennaio 2006 e aprile 2013. H.10 ne presenta 57: la sospensione della
pubblicazione lascia 31 mesi consecutivi senza release, da giugno 2006 a
dicembre 2008. Il DDP/current bulk non e' ammesso come sostituto vintage.

Per FDIC la disponibilita' e' determinata dalla pubblicazione effettiva, non
dal quarter-end o dall'esistenza odierna del link. Con cutoff 2025-12-31 e lag
conservativo gia' congelato, 2025Q3 e' l'ultimo trimestre eleggibile; 2025Q4
resta post-cutoff. Le policy E14.7l non vengono rilassate. Di conseguenza non si
genera alcun request catalog e non si autorizza l'acquisizione. Il passo
successivo deve essere un redesign revisionato che sostituisca H.10 e definisca
la copertura FDIC per vintage di pubblicazione, preservando le due famiglie gia'
vintage-fit.

### E14.7n - Proposta di redesign e review indipendente

La proposta preserva byte-per-byte gli esiti E14.7l/E14.7m e le famiglie
`broad-market-repricing` e `funding-liquidity`. Per `cross-border-growth`
propone l'archivio mensile G.5: il calendario provider-primary copre 88 mesi su
88 prima del taper tantrum e le release legacy contengono Broad e OITP. Il
cambio metodologico effettivo dal 2019-02-04 crea regimi separati; nessuno
splice o uso event-time della backhistory ricalcolata e' consentito.

Per FDIC, un trimestre e' eleggibile soltanto quando una statement/release
contemporanea o un timestamp provider-primary equivalente prova la data reale
di pubblicazione. Q3 2025 e' eleggibile dal 2025-11-24; Q4 2025 resta fuori dal
cutoff. Due dossier immutabili e una queue senza receipt aprono esclusivamente
l'handoff alla review indipendente. Nessuna policy viene attivata e nessun dato
viene acquisito.

### E14.7o - Gate di compatibilita' dell'handoff

Prima di generare worksheet o template, il gate deve dimostrare che una receipt
completata puo' essere simultaneamente valida rispetto allo schema congelato e
legata all'ID/hash esatto della queue. Un alias non e' ammesso. Nel caso E14.7n
entrambi gli ID falliscono il pattern v2 `^e14-dossier-[a-z0-9-]+$`; anche la
semantica `counterEvidenceConsidered=true` non coincide con la struttura dei
dossier redesign. Il gate pubblica quindi soltanto un audit immutabile bloccato,
con inventario bundle/template/receipt a zero. Ogni autorizzazione downstream
resta falsa finche' uno schema e un evidence contract versionati non superano
nuovamente il gate.

### E14.7p - Remediation versionata del contratto di review

La remediation non cambia i bytes dei dossier E14.7n. Una queue v2 supersede
la queue incompatibile per hash e lega uno schema receipt dedicato e un evidence
contract esterno. Ogni receipt deve includere gli hash esatti di dossier, queue,
evidence contract e schema, oltre agli assessment nominativi di tutti i finding
e di tutta la counterevidence. Un accept richiede locator aperti, tutti i
finding supportati, counterevidence considerata e nessun model output.

Il contratto include sette locator provider-primary: calendario e due release
G.5 legacy, nota metodologica Fed, policy QBP e statement FDIC Q3/Q4 2025. La
pubblicazione Q4 del 2026-02-24 prova direttamente l'esclusione al cutoff
2025-12-31. E14.7p materializza solo queue v2 e audit; bundle, receipt,
ingestion, attivazione e ogni lavoro sui dati restano separati e chiusi.

### E14.7q - Handoff immutabile al reviewer indipendente

Il bundle viene costruito soltanto dopo un preflight completo di input, path e
destinazioni. Proposta, queue v2, dossier, evidence contract, schema dedicato e
remediation audit sono copiati byte-identici. Il manifest esterno registra per
ogni file path relativo, ruolo, SHA-256 e dimensione.

Ogni worksheet elenca quattro finding, tutti i locator anche quando ripetuti
per ruoli distinti, e la counterevidence nominativa. Ogni template contiene i
binding esatti ma placeholder/null che lo rendono non ingeribile. Il reviewer
deve copiarlo fuori dal bundle prima di compilarlo. Il generatore non produce
receipt, non svolge review e non autorizza ingestion o policy activation.

### E14.7r - Ingestion fail-closed della review indipendente

L'ingestion accetta soltanto due file JSON regolari, uno per dossier, fuori dal
bundle immutabile. Ogni receipt deve legare gli hash canonici di dossier, queue
v2, evidence contract e schema dedicato; il reviewer deve differire dall'autore
della proposta e dichiarare l'indipendenza. Un `accept` richiede tutti i finding
supportati, tutti i locator aperti, la counterevidence considerata e nessun
model output.

Le due receipt autentiche accettano entrambi i redesign. La queue v3 registra
le decisioni senza mutare le receipt. Output dentro receipt, dossier o bundle,
entry inattese, symlink, hash errati e pubblicazioni parziali falliscono chiusi.
L'esito autorizza esclusivamente un gate di attivazione policy separato:
request catalog, acquisizione, trasformazione, candidati, evaluation e outer
OOS restano vietati.

### E14.7s - Attivazione dell'overlay source-vintage policy v2

Il gate lega per hash canonico proposta e proposal audit, queue v3, ingestion
audit, taxonomy post-2005 attiva, scope activation audit e piani versionati.
Non modifica taxonomy o label: pubblica un overlay immutabile specifico per la
policy di sorgente e vintage.

Per `cross-border-growth`, H.10 viene ritirato e G.5 e' attivo con storia
percentile separata fra regime legacy Broad/OITP e regime Broad/AFE/EME; splice
e backcast event-time restano vietati. Per `banking-credit`, l'eleggibilita'
FDIC richiede prova provider-primary della data reale di pubblicazione. I
vecchi manifest e snapshot H.10 non soddisfano la policy v2 e non vengono
reinterpretati.

Il gate autorizza soltanto il prossimo step separato di preregistrazione di un
manifest e request catalog versionati. Non genera il catalogo, non acquisisce
osservazioni e mantiene chiusi trasformazione, candidati, evaluation e outer
OOS.

### E14.7t - Manifest e request catalog source-vintage v2

Il manifest v2 supersede per provenienza il manifest v1 senza modificarlo. Il
roster resta di sette sorgenti: H.8, FDIC QBP, DGS2, DGS10, G.5, DCPF3M e DTB3.
H.10 e i relativi raw path devono essere assenti da manifest e catalogo.

Il catalogo preregistra 11 template. Le espansioni di H.8, FDIC e G.5 possono
usare soltanto valori scoperti sulle pagine provider-primary. G.5 richiede 240
mesi unici tra 2006-01 e 2025-12 e ogni duplicato/correzione richiede
adjudication. FDIC richiede 79 trimestri da 2006Q1 a 2025Q3; 2025Q4 e'
esplicitamente escluso e il quarter-end non sostituisce la data di
pubblicazione.

La preregistrazione non esegue rete, non crea raw artifact e non autorizza
l'acquisizione. Il solo passo ammesso e' un gate metadata separato e
fail-closed contro gli hash esatti di manifest e catalogo v2.

### E14.7u - Gate metadata e autorizzazione separata

Il gate richiede gli hash canonici di manifest v2, request catalog v2 e audit
di preregistrazione. La credenziale FRED viene verificata solo in memoria. Ogni
probe e' HTTPS, limitato a 65.536 byte e vincolato per marker, content type e
intera catena di redirect; un redirect off-allowlist viene rifiutato prima
della richiesta.

L'audit v2 ha fallito chiuso sul marker del calendario G.5. Il piano v3 lega
per hash quell'audit e sostituisce esclusivamente `releaseDate` con il campo
provider-primary `MonthValue`. Il retry supera sette probe su sette. Il gate
esegue zero request template, non acquisisce osservazioni e non scrive raw
artifact. Autorizza solo il successivo executor atomico; trasformazione,
candidati, evaluation e outer OOS restano chiusi.

### E14.7v - Preflight discovery-first dell'acquisizione

Prima di qualsiasi richiesta event-time o FRED, l'executor esegue soltanto i
tre discovery URL congelati. Non segue calendari o archivi collegati ma non
preregistrati. Ogni payload deve rispettare marker, content type, limite byte e
provider-host pinning; i redirect off-provider sono rifiutati prima del follow.

La landing H.8 non contiene direttamente le 1.043 date, la landing FDIC non
contiene i 79 documenti ne' le 79 date effettive di pubblicazione, e il
calendario G.5 contiene due mesi duplicati che richiedono adjudication. Il
preflight rimuove lo staging e pubblica soltanto un audit bloccato. Full
acquisition, raw snapshot, trasformazione, candidati, evaluation e outer OOS
restano vietati finche' catalogo e adjudication non sono versionati.

### E14.7w - Docket di remediation review-first

Il docket sostituisce l'assunzione H.8 di 1.043 settimane con il conteggio
provider-primary di 1.042 release, senza autorizzare automaticamente il nuovo
requisito. Per FDIC congela il roster completo 79/79 ma mantiene il ledger
delle date di pubblicazione a 0/79: quarter-end, Last-Modified e lag stimati
restano sostituti vietati.

Per G.5 entrambe le versioni duplicate sono preservate. L'originale rimane
efficace fino alla data della correzione; nessuna correzione viene applicata
retroattivamente all'inizio del mese. Il docket pubblica solo proposta,
dossier, queue e audit. Catalogo v3, snapshot e qualsiasi esecuzione restano
assenti; il solo gate successivo e' la review indipendente.

### E14.7x - Review indipendente del docket

La review hash-bound accetta il conteggio H.8 di 1.042 release, il roster FDIC
79/79 con gap probatorio preservato a 0/79 e le catene G.5 senza retroattivita'.
La decisione non rende eseguibile il docket e non autorizza catalogo v3,
snapshot v2, rete, acquisizione o trasformazioni. Il solo passo successivo
ammesso e' la preregistrazione fail-closed di una raccolta metadata-only delle
79 prove provider-primary di pubblicazione FDIC, seguita da review separata.

### E14.7y - Preregistrazione raccolta metadata FDIC

Il gate congela un roster esatto di 79 quarter da 2006Q1 a 2025Q3 e richiede,
per ogni riga futura, data effettiva, URL provider-primary FDIC, tipo di
evidenza, hash della risposta e timestamp. Quarter-end, Last-Modified, lag
stimati e fonti secondarie non sono prove ammissibili.

La preregistrazione esegue zero richieste e raccoglie zero righe. Autorizza
soltanto la review indipendente del disegno di esecuzione metadata-only. Rete,
catalogo v3, snapshot v2, payload event-time e ogni fase downstream restano
chiusi fino a un gate separato.

### E14.7z - Review indipendente del disegno metadata FDIC

La review hash-bound accetta il roster 79/79, i campi di prova, i sostituti
vietati, il pinning a `www.fdic.gov` e i guard fail-closed. Conferma inoltre che
E14.7y ha effettuato zero richieste e raccolto zero righe.

La receipt non autorizza direttamente la rete. Il solo passo successivo e' un
gate di esecuzione separato che congeli limiti e comportamento operativo della
raccolta metadata-only. Catalogo v3, snapshot v2, payload event-time e
downstream restano vietati.

### E14.7aa - Gate operativo raccolta metadata FDIC

Il gate congela `www.fdic.gov` come unico host, budget 158 richieste logiche e
316 tentativi fisici, redirect same-host, timeout 30 secondi, limite 8 MiB,
content type HTML/PDF e retry soltanto sugli status transitori ammessi.
Redirect off-provider, content type errato e oversize falliscono senza retry.

Il gate esegue zero richieste. Autorizza soltanto il collector separato, che
puo' pubblicare mediante rename atomico esclusivamente un ledger completo e
validato 79/79. Ledger parziali, catalogo v3, snapshot v2, payload event-time e
downstream restano vietati.

### E14.7ab - Preflight fail-closed del collector FDIC

Prima della rete il collector deve trovare nel materiale hash-bound sia gli
URL seed esatti sia i template di richiesta. I soli limiti operativi non sono
sufficienti a rendere deterministica l'esecuzione.

Il piano E14.7aa non contiene tali elementi. Il preflight pubblica quindi un
audit bloccato con zero richieste, zero righe, zero raw artifact, zero ledger e
zero cataloghi. E' ammessa soltanto la preregistrazione versionata del request
catalog metadata-only; ogni variazione degli host ammessi richiede un nuovo
gate e review indipendente prima della raccolta.
