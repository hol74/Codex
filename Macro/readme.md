# Macro-Regime Engine

## Guida completa al progetto, alle scelte architetturali e alla governance

**Stato del documento:** aggiornato al 17 luglio 2026  
**Stato del progetto:** la fase E14.8 è conclusa come `design-complete` e `safely blocked`; la prima esecuzione prospettica completa di E9 resta subordinata al cutoff del 31 luglio 2026; la fase F non è ancora iniziata.

---

## Indice

1. [Il progetto in parole semplici](#1-il-progetto-in-parole-semplici)
2. [Obiettivo e confini](#2-obiettivo-e-confini)
3. [Le scelte fondamentali](#3-le-scelte-fondamentali)
4. [Che cosa produce il sistema](#4-che-cosa-produce-il-sistema)
5. [Come è strutturata la soluzione](#5-come-è-strutturata-la-soluzione)
6. [Come fluiscono dati e decisioni](#6-come-fluiscono-dati-e-decisioni)
7. [Il tempo dell'informazione e la prevenzione degli errori storici](#7-il-tempo-dellinformazione-e-la-prevenzione-degli-errori-storici)
8. [Modelli, regimi e incertezza](#8-modelli-regimi-e-incertezza)
9. [Dalla lettura del regime alla proposta di portafoglio](#9-dalla-lettura-del-regime-alla-proposta-di-portafoglio)
10. [Il laboratorio di ricerca e la validazione](#10-il-laboratorio-di-ricerca-e-la-validazione)
11. [Shadow Operations](#11-shadow-operations)
12. [Persistenza, integrità, rete e sicurezza](#12-persistenza-integrità-rete-e-sicurezza)
13. [Governance adottata](#13-governance-adottata)
14. [Processo formale di sviluppo e approvazione](#14-processo-formale-di-sviluppo-e-approvazione)
15. [Decisioni architetturali formalizzate](#15-decisioni-architetturali-formalizzate)
16. [Percorso svolto e stato delle fasi](#16-percorso-svolto-e-stato-delle-fasi)
17. [Che cosa significa la chiusura di E14.8](#17-che-cosa-significa-la-chiusura-di-e148)
18. [Che cosa resta da fare](#18-che-cosa-resta-da-fare)
19. [Rischi noti e contromisure](#19-rischi-noti-e-contromisure)
20. [Mappa dei documenti](#20-mappa-dei-documenti)
21. [Glossario degli acronimi](#21-glossario-degli-acronimi)
22. [Glossario dei concetti](#22-glossario-dei-concetti)

---

## 1. Il progetto in parole semplici

Il **Macro-Regime Engine** è un sistema informativo locale che aiuta a interpretare il contesto macroeconomico e finanziario. Il suo compito è rispondere, in modo documentato, a una domanda simile a questa:

> «Con le sole informazioni che erano realmente disponibili in una certa data, quali scenari economico-finanziari apparivano più probabili, perché, e quale adattamento prudente del portafoglio sarebbe stato compatibile con le regole stabilite?»

Il sistema non cerca una previsione infallibile e non restituisce un ordine di acquisto o vendita. Costruisce invece una **catena di evidenze**:

1. raccoglie o legge dati macroeconomici e di mercato;
2. stabilisce quando quei dati erano effettivamente conoscibili;
3. calcola indicatori omogenei, chiamati *feature*;
4. assegna una probabilità a più regimi possibili;
5. spiega quali segnali hanno sostenuto o contraddetto il risultato;
6. applica vincoli di rischio e di politica d'investimento;
7. produce una proposta, non una decisione automatica;
8. conserva dati, configurazioni, versioni e motivazioni per rendere il risultato verificabile in seguito.

Il valore principale non è quindi una singola etichetta, ma la **riproducibilità del ragionamento**. Una persona deve poter ricostruire che cosa il sistema sapeva, che cosa ha calcolato, con quale versione e in base a quali regole.

---

## 2. Obiettivo e confini

### 2.1 Obiettivo

L'obiettivo è costruire una pipeline professionale, governata e auditabile a supporto della strategia di portafoglio personale. La pipeline separa deliberatamente:

- i dati grezzi;
- la loro trasformazione in indicatori;
- la classificazione probabilistica del regime;
- l'eventuale proposta allocativa;
- i controlli di rischio;
- la decisione finale della persona responsabile.

### 2.2 Che cosa il sistema è

Il sistema è:

- uno strumento informativo e di ricerca;
- un archivio di analisi riproducibili nel tempo;
- un ambiente per confrontare un modello semplice con candidati più avanzati;
- un meccanismo di controllo che può rifiutarsi di procedere quando le evidenze sono insufficienti;
- un supporto alla decisione umana.

### 2.3 Che cosa il sistema non è

Il sistema non è:

- consulenza finanziaria;
- un motore di trading automatico;
- un esecutore di ordini;
- una garanzia di rendimento;
- un sistema che modifica liberamente il portafoglio sulla base di una previsione;
- una procedura che nasconde risultati negativi o corregge retroattivamente le regole dopo aver visto gli esiti.

L'approvazione finale resta umana. I vincoli della politica d'investimento prevalgono sempre sull'opinione del modello.

---

## 3. Le scelte fondamentali

### 3.1 Il regime è probabilistico

L'economia non passa tra stati perfettamente osservabili come un semaforo. Per questo il risultato contiene una distribuzione di probabilità, per esempio:

- regime A: 45%;
- regime B: 35%;
- regime C: 20%.

La somma deve essere coerente e l'incertezza non viene nascosta.

### 3.2 L'incertezza è uno stato valido

Quando i segnali sono deboli, discordanti, obsoleti o collocati in una transizione, il sistema deve poter restituire `UncertainTransition`. Non è un errore tecnico: è una conclusione prudente.

### 3.3 Macro, mercato e portafoglio sono livelli distinti

Tre domande non devono essere confuse:

1. **Macro regime:** in quale contesto economico potremmo trovarci?
2. **Market regime:** come stanno reagendo i mercati finanziari?
3. **Portfolio regime:** quali azioni sono consentite dalle regole del portafoglio?

Un quadro macro favorevole non implica automaticamente un acquisto; una situazione di mercato difficile non autorizza automaticamente una liquidazione.

### 3.4 Prima il modello semplice, poi i modelli avanzati

La **baseline rule-based**, cioè un insieme trasparente di regole, è il riferimento permanente. Modelli più complessi entrano come *challenger* e devono dimostrare un vantaggio fuori campione. Nel progetto, k-means e Gaussian HMM sono stati valutati e respinti: il risultato negativo è stato conservato.

### 3.5 Nessuna informazione dal futuro

Ogni analisi storica deve rispettare una data limite, detta *as-of date* o *information cutoff*. Sono ammessi soltanto i dati realmente disponibili entro quella data, compresa la versione storica allora pubblicata.

### 3.6 La proposta allocativa parte dalla politica esistente

Il sistema non costruisce un portafoglio da zero. Parte da:

- allocazione strategica;
- bande minime e massime;
- portafoglio corrente;
- limite di turnover;
- costi, fiscalità e liquidità rappresentabili;
- regole di prudenza.

Produce soltanto scostamenti limitati, spiegati e verificabili.

### 3.7 Il sistema può fermarsi in sicurezza

È stata adottata una filosofia **fail-closed**: se manca una prova obbligatoria, un hash non coincide, una review è negativa o una fonte non soddisfa il requisito temporale, la capacità successiva rimane chiusa.

---

## 4. Che cosa produce il sistema

Gli artefatti principali sono i seguenti.

### 4.1 Data Snapshot

Fotografia dei dati utilizzabili a una determinata data. Include valori, fonti e riferimenti temporali.

### 4.2 Feature Set

Insieme versionato degli indicatori calcolati dai dati. Ogni feature deve avere formula, frequenza, unità, trasformazione, polarità, lookback e versione.

### 4.3 Regime Snapshot o Regime Run

Risultato completo di un'esecuzione:

- data di analisi;
- modello e configurazione;
- probabilità dei regimi;
- regime primario e operativo;
- livello di confidenza;
- driver favorevoli e segnali contrari;
- warning;
- riferimenti ai dati e ai relativi hash.

### 4.4 Allocation Proposal

Proposta vincolata di variazione del portafoglio. Contiene pesi correnti, pesi strategici, pesi proposti, scostamenti, turnover, violazioni o warning e motivazione.

### 4.5 Report Markdown e pagine Web

Rappresentazioni leggibili degli artefatti già calcolati. Il livello di reporting non modifica il risultato.

### 4.6 Artefatti di Shadow Operations

- `PredictionLedger`: previsione congelata prima di conoscere l'esito;
- `PredictionScore`: valutazione successiva, quando l'esito è disponibile;
- `GateDecision`: decisione formale di accettare, respingere o mantenere bloccato un passaggio;
- `ShadowPreflight`: controlli precedenti al congelamento;
- `ShadowIndex`: indice derivato dei ledger esistenti.

---

## 5. Come è strutturata la soluzione

La soluzione usa una struttura a livelli. Ogni livello ha una responsabilità precisa e dipendenze controllate.

```text
MacroRegime.slnx
│
├── src/
│   ├── MacroRegime.Domain/
│   ├── MacroRegime.Application/
│   ├── MacroRegime.Infrastructure/
│   ├── MacroRegime.Reporting/
│   ├── MacroRegime.Cli/
│   └── MacroRegime.Web/
│
├── tests/
│   └── un progetto di test per ciascun livello principale
│
├── research/regime-eval/
│   └── laboratorio Python separato dal runtime
│
├── data/
│   └── input, snapshot, run e artefatti locali
│
└── docs/
    ├── adr/
    ├── architecture/
    ├── checkpoints/
    ├── domain/
    ├── planning/
    ├── releases/
    └── testing/
```

### 5.1 Domain

`MacroRegime.Domain` contiene il nucleo logico puro:

- oggetti temporali;
- snapshot e feature;
- tassonomia dei regimi;
- probabilità, confidenza e spiegazioni;
- baseline detector;
- politica allocativa, bande e proposta.

Deve essere deterministico e testabile senza database, file, rete, interfaccia grafica o orologio di sistema.

### 5.2 Application

`MacroRegime.Application` descrive i casi d'uso e le porte necessarie per interagire con l'esterno. Coordina il lavoro, ma non conosce i dettagli tecnici degli adapter.

Esempi: caricare un run, eseguire un'analisi, confrontare due run, scaricare dati attraverso una porta, validare un import.

### 5.3 Infrastructure

`MacroRegime.Infrastructure` contiene i dettagli sostituibili:

- lettura e scrittura JSON;
- archivi file-based;
- importazioni;
- client FRED, ALFRED e Yahoo;
- builder del dataset storico;
- adapter di persistenza e rete.

Può trasportare dati, ma non deve decidere il regime economico.

### 5.4 Reporting

`MacroRegime.Reporting` trasforma risultati esistenti in documenti leggibili. Non ricalcola il modello e non cambia i dati.

### 5.5 CLI

`MacroRegime.Cli` è l'interfaccia a riga di comando e il *composition root*: collega le implementazioni concrete ai casi d'uso. Le operazioni batch e di rete devono essere richieste esplicitamente qui.

### 5.6 Web

`MacroRegime.Web` è una dashboard locale di sola lettura. Mostra run, diagnostica e confronti; non scarica dati e non contiene formule di dominio.

### 5.7 Laboratorio Python

`research/regime-eval` è separato dal runtime C#. Serve per esperimenti, validazioni point-in-time, walk-forward, confronto baseline/challenger, model card e gate. Un esperimento Python non diventa automaticamente comportamento operativo.

### 5.8 Regole delle dipendenze

Sono consentite, in sintesi:

```text
Application    → Domain
Infrastructure → Application + Domain
Reporting      → Application + Domain
CLI / Web      → livelli necessari alla composizione o alla lettura
```

Sono vietate:

- dipendenze del Domain verso livelli esterni;
- dipendenza di Application da Infrastructure;
- formule di business nella Web UI;
- logica di classificazione negli adapter;
- download impliciti dal Web o dal nucleo applicativo.

Questa struttura evita che una modifica alla UI, a un file o a un provider cambi accidentalmente il significato economico del sistema.

---

## 6. Come fluiscono dati e decisioni

Un'esecuzione ordinaria segue formalmente questi passaggi:

1. **Richiesta.** L'utente indica la data di analisi e avvia il caso d'uso dalla CLI o dalla Web UI.
2. **Caricamento.** Application richiede, tramite porte, snapshot dati, feature set, versione modello, politica e portafoglio corrente.
3. **Validazione.** Si verificano completezza, unità, frequenza, date, versioni, configurazioni e vincoli.
4. **Normalizzazione.** Il Domain trasforma gli indicatori nel formato atteso dal modello.
5. **Classificazione.** Il detector calcola la distribuzione di probabilità dei regimi.
6. **Spiegazione.** Vengono prodotti driver, segnali contrari, confidenza e warning.
7. **Politica allocativa.** Solo dopo la classificazione, il Domain applica bande e limiti e costruisce una proposta prudente.
8. **Persistenza.** Infrastructure salva il `RegimeRun` in JSON.
9. **Reporting.** Reporting genera il documento Markdown e Web rende visibili gli artefatti.
10. **Indicizzazione.** Un manifest derivato facilita la ricerca senza diventare la fonte primaria.
11. **Decisione umana.** Il proprietario valuta la proposta e registra la decisione; il sistema non esegue ordini.

La separazione rende visibile dove nasce ogni informazione e chi è autorizzato a modificarla.

---

## 7. Il tempo dell'informazione e la prevenzione degli errori storici

I dati economici hanno più date, tutte importanti.

### 7.1 Observation Date

È il periodo economico descritto. Un dato può riferirsi, per esempio, a gennaio.

### 7.2 Publication Date

È la data in cui l'organizzazione responsabile pubblica il dato.

### 7.3 Availability Date

È il momento in cui il dato diventa effettivamente acquisibile e utilizzabile dal sistema.

### 7.4 As-of Date o Information Cutoff

È il confine della conoscenza consentita. Per un'analisi al 31 gennaio non si può usare una revisione pubblicata a marzo, anche se riferita a gennaio.

### 7.5 Vintage

È la specifica versione storica di una serie. Molti indicatori macroeconomici vengono revisionati; il valore conosciuto allora può differire da quello visibile oggi.

### 7.6 Regola point-in-time

Un input è ammesso soltanto se la sua disponibilità è anteriore o uguale al cutoff. Dove possibile si usano vintage storici, in particolare tramite ALFRED. Quando una fonte non offre una ricostruzione completa, il limite viene dichiarato e non mascherato.

### 7.7 Perché è indispensabile

Usare oggi il valore corretto e revisionato per simulare una decisione passata produce **look-ahead bias**: il modello sembra più intelligente perché riceve informazioni che allora non esistevano. Tutta la fase E è stata progettata per ridurre questo rischio.

---

## 8. Modelli, regimi e incertezza

### 8.1 Tassonomia dei regimi

La tassonomia corrente comprende concetti come:

- `Goldilocks`: crescita equilibrata e inflazione contenuta;
- `Reflation`: crescita o ripresa accompagnata da pressioni inflazionistiche crescenti;
- `LateCycleOverheating`: fase matura con surriscaldamento;
- `Stagflation`: inflazione elevata e crescita debole;
- `DeflationBust`: contrazione severa con pressioni deflazionistiche o recessive;
- `ZirpQeFinancialRepression`: tassi eccezionalmente bassi, politiche quantitative e compressione dei rendimenti;
- `UncertainTransition`: transizione o conflitto informativo non risolvibile con sufficiente affidabilità.

Le etichette sono strumenti di sintesi, non descrizioni assolute della realtà.

### 8.2 Primary Regime e Operational Regime

Il **Primary Regime** è il regime con probabilità più alta. L'**Operational Regime** è quello utilizzabile operativamente dopo aver applicato soglie di confidenza e regole di prudenza. Possono differire: un vincitore matematico debole può essere trasformato in `UncertainTransition`.

### 8.3 Baseline rule-based

La baseline utilizza regole esplicite, pesi e soglie versionati. È leggibile, riproducibile e costituisce:

- il benchmark minimo;
- uno strumento diagnostico;
- il fallback;
- il riferimento che ogni challenger deve superare.

La baseline v1.4 ha superato i gate tecnici stabiliti nel laboratorio, ma ciò non equivale a prova definitiva o promozione automatica all'uso allocativo.

### 8.4 Challenger

Un challenger è un modello sperimentale confrontato con la baseline usando lo stesso protocollo. Nel progetto sono stati provati:

- clustering k-means;
- Gaussian HMM;
- varianti a doppia scala temporale;
- candidati event-aware e disegni informativi successivi.

Quando non hanno superato i criteri preregistrati, sono stati respinti senza modificare retroattivamente il test.

### 8.5 Spiegabilità

Ogni risultato deve mostrare:

- indicatori che hanno contribuito;
- intensità e direzione del contributo;
- segnali contrari;
- dati mancanti o vecchi;
- livello di confidenza;
- versione del modello.

La spiegazione non è una decorazione: è un requisito di governance.

---

## 9. Dalla lettura del regime alla proposta di portafoglio

Il motore allocativo è subordinato all'**IPS**, cioè alla politica d'investimento. Il procedimento previsto è:

1. leggere l'allocazione strategica di lungo periodo;
2. leggere il portafoglio corrente;
3. applicare soltanto i tilt autorizzati dal regime operativo;
4. rispettare le bande minime e massime per classe di attivo;
5. limitare il turnover;
6. rappresentare costi, fiscalità e liquidità;
7. penalizzare soluzioni estreme;
8. ridurre l'aggressività quando confidenza o qualità dei dati sono basse;
9. produrre una proposta motivata;
10. lasciare la decisione finale alla persona responsabile.

Sono vietate logiche implicite di tipo “tutto dentro” o “tutto fuori”. La futura fase F dovrà rendere più rigorosa l'ottimizzazione, ma non potrà eliminare questi vincoli.

---

## 10. Il laboratorio di ricerca e la validazione

### 10.1 Perché è separato

La ricerca richiede libertà di sperimentazione; il runtime richiede stabilità. Tenere Python separato da C# impedisce che un notebook o un esperimento modifichi accidentalmente il comportamento operativo.

### 10.2 Dataset storico

È stato costruito un corpus mensile macro e market, attualmente concentrato sul periodo 2008-2025. I dati provengono da fonti dichiarate, sono accompagnati da manifest e hash e vengono controllati prima della valutazione.

### 10.3 Walk-forward validation

La valutazione procede nel tempo:

1. addestramento su una finestra storica di 10 anni;
2. test sui 2 anni successivi;
3. avanzamento di 1 anno;
4. ripetizione su più fold.

Il futuro non entra nell'addestramento del passato.

### 10.4 Train Gate

Prima di osservare i risultati fuori campione, un modello deve superare controlli sul solo training. In caso contrario viene respinto senza “curarlo” usando il test.

### 10.5 Out-of-Sample

La valutazione OOS misura il comportamento su dati non usati per calibrare il modello. Le metriche includono, secondo il caso, log loss, Brier score, precision, recall, F1, stabilità, ritardo di rilevazione e comportamento condizionato dei rendimenti.

### 10.6 Ground truth e limiti

Per le recessioni si usa la cronologia NBER come riferimento ex-post. Essa è autorevole per la datazione storica, ma non era disponibile in tempo reale e non descrive tutti gli stress finanziari. Per questo sono stati introdotti anche dossier e cronologie multi-label, mantenendo espliciti limiti e provenienza.

### 10.7 LOEO e test sugli episodi

La validazione `Leave-One-Episode-Out` esclude a turno un intero episodio di crisi. Serve a verificare se una regola riconosce caratteristiche generali o ricorda soltanto gli episodi già osservati.

### 10.8 Conservazione dei risultati negativi

Un `no-go` è un risultato valido. Configurazione, metriche e motivazione vengono conservate. Questo riduce il rischio di scegliere soltanto esperimenti favorevoli.

---

## 11. Shadow Operations

Le Shadow Operations verificano il sistema in tempo reale senza usarlo per prendere automaticamente decisioni di portafoglio.

### 11.1 Separazione tra previsione ed esito

La procedura è intenzionalmente divisa:

1. alla chiusura del mese si genera una previsione;
2. la previsione viene congelata senza outcome futuro;
3. soltanto più avanti si acquisisce l'esito;
4. si calcola lo score in un artefatto separato;
5. una decisione di gate valuta le evidenze.

In questo modo non è possibile riscrivere facilmente la previsione dopo aver visto il risultato.

### 11.2 Preflight

Prima del congelamento, `ShadowPreflight` verifica almeno:

- mese effettivamente chiuso;
- integrità e hash degli input;
- assenza di rendimenti futuri o label;
- presenza delle serie richieste;
- freschezza dei dati;
- coerenza tra configurazione ed evaluation;
- fingerprint del codice C# e Python.

### 11.3 Stati dell'orchestrazione

Il ciclo mensile attraversa stati espliciti, per esempio:

```text
initialized/resuming
        ↓
population → dataset → evaluation → preflight
        ↓
prepared, se richiesto prepare-only
        ↓
ledger/index
        ↓
ledger-frozen, per un ciclo full riuscito
```

Se non esiste un mese eleggibile, non viene lanciato alcun comando. I retry devono essere idempotenti; se un artefatto già presente è diverso, si genera un conflitto invece di sovrascriverlo.

### 11.4 Stato corrente di E9

La macchina operativa e i controlli sono stati implementati. La prima prova prospettica completa dipende però dal primo cutoff utile dopo la chiusura del mese, attualmente il **31 luglio 2026**. Fino a tale evento la fase E non può essere considerata integralmente chiusa sul piano prospettico.

---

## 12. Persistenza, integrità, rete e sicurezza

### 12.1 Persistenza file-based

La persistenza ufficiale usa file JSON e Markdown. È una scelta deliberata, non una soluzione provvisoria inconsapevole. Offre:

- semplicità;
- portabilità;
- ispezionabilità;
- versionamento e backup agevoli;
- riproducibilità locale.

Un database sarà rivalutato soltanto in presenza di trigger concreti: molte relazioni, query interattive complesse, volume elevato, concorrenza di scrittura o workflow decisionali multiutente.

### 12.2 Write-once e viste derivate

Gli artefatti autorevoli sensibili sono scritti una sola volta. Indici, manifest di consultazione e stato del ciclo possono essere ricostruiti e quindi non prevalgono sull'artefatto primario.

### 12.3 Hash SHA-256

Un hash identifica il contenuto. Se cambia anche un solo byte, cambia l'impronta. Serve a legare tra loro dati, configurazioni, report e review.

L'hash dimostra coerenza del contenuto, ma da solo non dimostra che il dato sia economicamente corretto, non sostituisce una firma digitale e non impedisce a un attore con accesso completo di sostituire file e hash insieme.

### 12.4 Isolamento della rete

La rete è confinata in Infrastructure e viene attivata esplicitamente dalla CLI. Domain, Application e Web non scaricano dati. Questo evita download invisibili durante un calcolo o durante la semplice consultazione di una pagina.

### 12.5 Segreti

API key e credenziali non devono apparire in repository, log, ricevute o argomenti persistiti. Gli artefatti temporanei non devono diventare fonti autorevoli.

### 12.6 Limite del solo filesystem locale

Un workspace locale copiabile non può impedire in assoluto un rollback coordinato: chi controlla tutti i file può ripristinare insieme dati, ricevute e indici. Le fasi E14.7 ed E14.8 hanno formalizzato questo limite invece di fingere che non esista.

### 12.7 Autorità monotona esterna: solo design

E14.8 ha congelato il disegno provider-neutral di una futura autorità esterna con:

- stati `ABSENT`, `PENDING`, `COMMITTED`;
- operazioni di lettura, confronto-e-scambio, commit e recovery;
- versioni monotone;
- catena di ricevute autenticate;
- chiavi di idempotenza;
- gestione di crash e retry;
- protezione dal rollback;
- controlli di durabilità e identità del processo;
- 14 scenari futuri obbligatori di conformità.

Non è stato selezionato alcun provider, non sono state create credenziali o risorse remote e non è stato implementato un adapter operativo.

---

## 13. Governance adottata

La governance stabilisce chi decide, quali prove servono e quando un risultato può avanzare.

### 13.1 Principi non negoziabili

1. Il regime è probabilistico.
2. Macro, mercato e portafoglio restano separati.
3. `UncertainTransition` è obbligatorio quando l'evidenza non è sufficiente.
4. La baseline precede i modelli avanzati.
5. HMM, clustering, Markov e ML entrano inizialmente come challenger.
6. Ogni run deve essere ricostruibile alla sua as-of date.
7. L'allocazione è subordinata a IPS, bande, turnover, costi, fiscalità e liquidità.
8. Strategie estreme sono vietate senza una policy esplicita.
9. Va registrato ciò che era noto al momento della decisione.
10. Il Domain deve restare testabile senza dipendenze esterne.

### 13.2 Responsabilità logiche

**Macro-Regime Information System**

- calcola feature, probabilità, driver e snapshot;
- non stabilisce autonomamente i pesi finali del portafoglio.

**Allocation Policy Engine**

- applica politica, bande, tilt e vincoli;
- non può ignorare l'ancora strategica.

**Decision and Governance Layer**

- registra versioni, run, review, decisioni umane e blocchi di rischio;
- stabilisce quali capacità sono autorizzate.

### 13.3 Ruoli

**Proprietario umano**

- approva principi, IPS e compromessi;
- approva o respinge la promozione dei modelli;
- prende la decisione allocativa finale.

**Agente di sviluppo**

- esegue il piano in incrementi verificabili;
- implementa test e documentazione;
- segnala limiti e rischi;
- non anticipa rete, modelli o ottimizzazioni non autorizzate.

**Baseline**

- resta benchmark e fallback permanente.

**Challenger**

- resta sperimentale finché non supera i gate e non riceve approvazione.

**Reviewer indipendente**

- valuta il contratto congelato;
- può restituire `accept`, `needs_changes` o un blocco;
- non deve trasformare la review in un'autorizzazione implicita a capacità successive.

### 13.4 Gate formali

#### Design Gate

Richiede problema, alternative, scelta, impatto e rispetto dei layer. Una decisione materiale produce un'ADR.

#### Data Gate

Richiede fonte, frequenza, unità, dimensione economica, polarità, date, vintage e regole complete delle feature.

#### Model Gate

Richiede scopo, dati, feature, frequenza, parametri, soglie, periodo, metriche, limiti, gestione di `UncertainTransition` e confronto con la baseline.

#### Allocation Gate

Richiede allocazione strategica, bande, turnover massimo, costi, fiscalità rappresentabile, liquidità, motivazione e assenza di violazioni della policy.

#### Release Gate

Richiede build e test verdi, demo o artefatti verificabili, report, documentazione aggiornata, limiti dichiarati e nessuna deviazione non documentata.

### 13.5 Ritmo di revisione

- review leggera a ogni milestone;
- review tecnica per architettura e modelli;
- revisione trimestrale dei modelli;
- revisione annuale della politica;
- revisione straordinaria dopo drawdown, problemi di liquidità, cambi fiscali o fallimenti rilevanti.

---

## 14. Processo formale di sviluppo e approvazione

Ogni incremento segue una sequenza controllata.

### 14.1 Definizione

Si dichiarano:

- obiettivo;
- perimetro incluso ed escluso;
- input e output;
- rischi;
- criterio di accettazione;
- Definition of Done.

### 14.2 Preregistrazione

Per gli esperimenti sensibili si congelano prima dell'esito:

- ipotesi;
- dataset;
- trasformazioni;
- parametri;
- metriche;
- soglie di promozione o rifiuto;
- azioni autorizzate dopo la review.

### 14.3 Implementazione minima

Si realizza il più piccolo incremento che produca un artefatto verificabile. Le capacità non richieste restano chiuse.

### 14.4 Verifica

Si eseguono test proporzionati al rischio:

- unit test del dominio;
- test applicativi;
- test degli adapter;
- test Web;
- test di integrazione locale;
- test anti-leakage e walk-forward nel laboratorio;
- test di integrità, idempotenza e recovery per Shadow Operations.

### 14.5 Review

Il reviewer confronta l'implementazione con il contratto congelato. Se l'esito è `needs_changes`, si crea una remediation versionata e una nuova review; non si sovrascrive la storia.

### 14.6 Checkpoint

Ogni passo chiuso genera un documento in `docs/checkpoints/` con:

- data;
- obiettivo;
- attività svolte;
- artefatti;
- verifiche;
- esito;
- limiti;
- unico passo successivo eventualmente autorizzato.

### 14.7 Fail-closed

L'accettazione apre soltanto ciò che è indicato esplicitamente. Non autorizza automaticamente rete, pubblicazione, downstream, modifica del runtime o uso allocativo.

### 14.8 Tracciamento delle modifiche

Una modifica a feature, soglia, modello o scope deve indicare prima/dopo, motivazione e impatto. La promozione richiede metriche predefinite, prova OOS, stress test, model card, spiegazioni e approvazione umana.

---

## 15. Decisioni architetturali formalizzate

Le decisioni importanti sono registrate come ADR.

### ADR 0001 — Restart architetturale

Il primo prototipo nel progetto Finance aveva dimostrato il valore dell'idea, ma mescolava detector, Infrastructure ed Entity Framework Core. È stato deciso un restart selettivo e document-first: riutilizzare la conoscenza, non l'accoppiamento tecnico.

### ADR 0002 — Dipendenze tra layer

Sono state fissate le direzioni consentite tra Domain, Application, Infrastructure, Reporting, CLI e Web. La logica economica resta nel nucleo.

### ADR 0003 — Persistenza file-based

JSON e Markdown restano la persistenza ufficiale finché non emerge un trigger reale per un database. Un cambio richiederà una nuova ADR.

### ADR 0004 — Isolamento della rete

I client HTTP vivono in Infrastructure e vengono composti esplicitamente dalla CLI. Il Web e i layer core consumano dati locali e non avviano download.

---

## 16. Percorso svolto e stato delle fasi

### Fondazioni

- ricerca iniziale e stato dell'arte;
- post-mortem del prototipo;
- restart architetturale;
- glossario, ADR, disegno del dominio e piano di test;
- implementazione del vertical slice C#;
- CLI, Web read-only, import locale, reporting e manifest.

### Fase A — Storico e confronto run

Completata. Il sistema legge run salvati senza rieseguire il modello e confronta due analisi storiche.

### Fase B — Import e diagnostica

Completata. Sono disponibili validazione degli input, diagnostica leggibile e batch multi-data.

### Fase C — Scelta della persistenza

Completata. La persistenza file-based è stata formalizzata come scelta stabile.

### Fase D — Dati esterni e dataset

Completata per il perimetro previsto. Sono stati introdotti adapter FRED/ALFRED, Yahoo, calendario delle release, vintage e dataset storico macro-market.

### Fase E1-E8 — Fondazione della valutazione

Completate. Comprendono Data Gate, corpus storico, walk-forward, baseline, ground truth NBER, challenger clustering e HMM, redesign baseline v1.4 e contratti separati di previsione, scoring e decisione.

### Fase E9 — Shadow Operations

Implementata sul piano tecnico, ma in attesa della prima esecuzione prospettica full al cutoff utile del 31 luglio 2026. È il vincolo temporale che impedisce di dichiarare conclusa l'intera fase E.

### Fasi E10-E13 — Candidati controllati

Completate come ricerca. Varianti dual-timescale, event-aware e LOEO non hanno superato i criteri necessari alla promozione. I `no-go` sono parte dell'evidenza.

### Fase E14 — Ridisegno della fondazione informativa

Ha rafforzato governance delle fonti, vintage, metadati, tassonomia post-2005 e protocolli di acquisizione/review.

- **E14.7:** chiusa `safely blocked`. La review finale ha accettato il confine fail-closed; pubblicazione e downstream restano non autorizzati.
- **E14.8:** chiusa `design-complete` e `safely blocked`. È stato accettato il disegno del futuro provisioning di un'autorità esterna, senza creare alcuna capacità operativa.

### Fase F — Ottimizzazione e stress

Non iniziata. È l'ultima fase funzionale pianificata, ma non parte automaticamente dalla chiusura documentale di E14.8: occorre prima rispettare il vincolo prospettico di E9 e formalizzare la chiusura della fase E.

---

## 17. Che cosa significa la chiusura di E14.8

La chiusura di E14.8 significa che il **disegno** è sufficientemente preciso e revisionato. In particolare:

- le dieci evidenze di provisioning sono obbligatorie;
- la macchina a stati e le operazioni sono definite;
- il protocollo è indipendente da uno specifico fornitore;
- sono congelati 14 scenari di conformità futuri;
- la review finale ha esito `accept`.

Non significa invece che:

- sia stato scelto un provider;
- esista un'autorità remota;
- siano state create credenziali;
- sia presente un adapter;
- la rete sia autorizzata;
- si possa pubblicare;
- i processi downstream siano aperti;
- il modello sia promosso all'allocazione.

La formula `safely blocked` indica quindi una conclusione positiva di governance: sappiamo esattamente perché la capacità resta chiusa e quali prove serviranno per aprirla in futuro.

---

## 18. Che cosa resta da fare

### 18.1 Prima di chiudere la fase E

Il passo temporalmente necessario è la prima esecuzione prospettica completa di E9 al cutoff del 31 luglio 2026, dopo la chiusura del mese e la disponibilità degli input. Dovrà essere seguita dal checkpoint di chiusura della fase E.

Un'eventuale selezione del provider per l'autorità esterna è una fase separata e non è stata autorizzata da E14.8.

### 18.2 Fase F

La fase F pianificata comprende quattro blocchi:

1. **Ottimizzazione allocativa vincolata:** bande IPS, turnover, costi, fiscalità, penalità per estremi e shrinkage degli expected return.
2. **Stress test storici:** 1973-74, 2000-02, 2008-09, 2020 e 2022.
3. **Stress fattoriali:** tassi +300 punti base, spread HY +500 punti base, USD +20%, azioni -35%, correlazioni portate a 1.
4. **Reverse stress test:** ricerca delle condizioni che provocherebbero il rischio primario, cioè una liquidazione forzata in un momento avverso.

Il dataset attuale parte sostanzialmente dal 2008: gli stress più antichi richiederanno un'estensione dati governata, non una semplice simulazione improvvisata.

---

## 19. Rischi noti e contromisure

| Rischio | Effetto possibile | Contromisura adottata |
|---|---|---|
| Look-ahead bias | Prestazioni storiche artificialmente alte | As-of date, vintage, Data Gate, point-in-time |
| Overfitting | Modello adatto al passato ma fragile | Baseline semplice, walk-forward, train gate, LOEO |
| Opacità | Decisione non spiegabile | Driver, segnali contrari, model card, versioni |
| Data leakage | Informazione futura nel training | Split temporali e test anti-leakage |
| Eccesso di turnover | Costi, tasse e instabilità | Limite di turnover, isteresi, cooldown |
| Portafogli estremi | Rischio incompatibile con la policy | IPS, bande, shrinkage, penalità |
| Confusione tra macro e portafoglio | Azioni non giustificate | Tipi, layer e responsabilità distinti |
| UI prematura | Logica dispersa nell'interfaccia | Domain-first e Web read-only |
| Riscrittura del passato | Valutazione non credibile | Write-once, hash, ledger separato dallo score |
| Rollback locale coordinato | Sostituzione coerente di file e indici | Limite dichiarato e design di autorità monotona esterna |
| Fonte incompleta | Ricostruzione temporale falsa | Fail-closed, dossier di fonte e review |
| Ricerca infinita | Nessun rilascio verificabile | Milestone piccole, DoD, gate e checkpoint |
| Automazione eccessiva | Decisione senza responsabilità | Approvazione umana obbligatoria |

---

## 20. Mappa dei documenti

Questo `readme.md` è la guida narrativa generale. Le fonti formali di dettaglio restano:

- [Piano operativo](docs/0001-piano-operativo.md)
- [Riepilogo del lavoro](docs/0002-riepilogo-lavoro-svolto.md)
- [Architettura, scelte e letteratura](docs/architecture/0001-architettura-sistema-scelte-letteratura-glossario.md)
- [Governance del progetto](docs/planning/0003-governance-progetto.md)
- [Glossario di dominio](docs/domain/0001-macro-regime-glossary.md)
- [ADR 0001 — Restart](docs/adr/0001-restart-architetturale.md)
- [ADR 0002 — Dipendenze](docs/adr/0002-dipendenze-layer.md)
- [ADR 0003 — Persistenza](docs/adr/0003-persistenza-locale-file-based.md)
- [ADR 0004 — Rete](docs/adr/0004-isolamento-rete-adapter-fred.md)
- [Checkpoint E14.8 finale](docs/checkpoints/0145-fase-e14-8c-provisioning-design-review-accepted.md)
- [README del laboratorio di ricerca](research/regime-eval/README.md)

In caso di differenza, il contratto o checkpoint specifico e più recente prevale sulla sintesi generale.

---

## 21. Glossario degli acronimi

| Acronimo | Espansione | Significato nel progetto |
|---|---|---|
| ADR | Architecture Decision Record | Documento che registra contesto, scelta, alternative e conseguenze di una decisione architetturale. |
| ALFRED | Archival Federal Reserve Economic Data | Servizio della Federal Reserve Bank of St. Louis che permette di recuperare versioni storiche dei dati FRED. |
| API | Application Programming Interface | Contratto tecnico con cui due componenti software comunicano; può richiedere una API key. |
| ASP.NET Core | Active Server Pages .NET Core | Framework Microsoft usato per la dashboard Web locale. |
| BAA10Y | Moody's Seasoned Baa Corporate Bond Yield Relative to 10-Year Treasury | Codice FRED usato come proxy dello spread creditizio tra obbligazioni societarie Baa e Treasury decennale. |
| BIS | Bank for International Settlements | Banca dei regolamenti internazionali, fonte istituzionale per dati e analisi finanziarie. |
| CAS | Compare-And-Swap | Operazione atomica che modifica uno stato soltanto se la versione corrente coincide con quella attesa. |
| CI | Continuous Integration | Esecuzione automatica di build e test a ogni cambiamento rilevante. |
| CLI | Command-Line Interface | Interfaccia a riga di comando usata per avviare analisi, import, download espliciti e batch. |
| CP | Commercial Paper | Debito a breve termine emesso da imprese o intermediari; alcuni spread CP sono segnali di stress. |
| CPI | Consumer Price Index | Indice dei prezzi al consumo, misura comune dell'inflazione. |
| DDD | Domain-Driven Design | Approccio che organizza il software attorno al dominio e al suo linguaggio condiviso. |
| DGS2 / DGS10 | 2-Year / 10-Year Treasury Constant Maturity Rate | Codici FRED dei rendimenti Treasury a 2 e 10 anni. |
| DoD | Definition of Done | Elenco verificabile delle condizioni necessarie per dichiarare chiuso uno step. |
| DTO | Data Transfer Object | Oggetto usato per trasferire dati tra confini senza incorporare logica di dominio. |
| EF Core | Entity Framework Core | Tecnologia Microsoft per accesso ai database; rimossa dal nucleo dopo il restart. |
| FDIC | Federal Deposit Insurance Corporation | Agenzia statunitense; il suo Quarterly Banking Profile è una fonte per il settore bancario. |
| F1 | F1 score | Media armonica di precision e recall; non è un acronimo, ma una metrica di classificazione. |
| FRED | Federal Reserve Economic Data | Banca dati economica della Federal Reserve Bank of St. Louis. |
| FRED-MD | FRED Monthly Database | Dataset mensile ad alta dimensionalità derivato dall'ecosistema FRED e usato come riferimento di ricerca. |
| H.8 | Assets and Liabilities of Commercial Banks in the United States | Pubblicazione statistica settimanale della Federal Reserve sul sistema bancario commerciale. |
| H.10 | Foreign Exchange Rates | Pubblicazione statistica della Federal Reserve sui cambi. |
| HMM | Hidden Markov Model | Modello probabilistico con stati latenti e transizioni temporali; valutato come challenger. |
| HTTP | Hypertext Transfer Protocol | Protocollo di rete usato dagli adapter esterni; vietato nei layer core. |
| HY | High Yield | Obbligazioni a rendimento elevato e merito creditizio più basso; lo spread è un indicatore di rischio. |
| ID | Identifier | Identificatore univoco di artefatti, run, modelli o richieste. |
| INDPRO | Industrial Production Index | Codice FRED della produzione industriale statunitense. |
| IPS | Investment Policy Statement | Documento di politica d'investimento che fissa obiettivi, rischi, bande e vincoli. |
| JSON | JavaScript Object Notation | Formato testuale strutturato usato per input, configurazioni, run e ricevute. |
| LOEO | Leave-One-Episode-Out | Validazione che esclude a turno un intero episodio per misurare la generalizzazione. |
| ML | Machine Learning | Famiglia di metodi che apprendono strutture dai dati; nel progetto entra inizialmente come challenger. |
| NBER | National Bureau of Economic Research | Organizzazione che data ufficialmente i cicli recessivi statunitensi ex-post. |
| OOS | Out-of-Sample | Periodo non usato per stimare o calibrare il modello. |
| PID | Process Identifier | Identificatore del processo operativo, utile per lock e recovery. |
| QBP | Quarterly Banking Profile | Rapporto trimestrale FDIC sul sistema bancario assicurato. |
| QE | Quantitative Easing | Acquisti di attività finanziarie da parte della banca centrale per allentare le condizioni monetarie. |
| SHA-256 | Secure Hash Algorithm, 256 bit | Funzione crittografica usata per produrre impronte dei contenuti. |
| SOFR | Secured Overnight Financing Rate | Tasso overnight garantito, riferimento del mercato monetario in dollari. |
| SPKI | Subject Public Key Info | Formato standard per rappresentare una chiave pubblica e il relativo algoritmo. |
| TLS / mTLS | Transport Layer Security / mutual TLS | Protezione del canale; in mTLS entrambe le parti si autenticano. Rilevante per una futura autorità esterna, non attiva oggi. |
| UI | User Interface | Interfaccia utente; nel progetto la Web UI è locale e di sola lettura. |
| URL | Uniform Resource Locator | Indirizzo di una risorsa o endpoint. |
| USD | United States Dollar | Dollaro statunitense, usato anche negli scenari di stress. |
| VIX | Cboe Volatility Index | Indicatore delle aspettative di volatilità implicita sull'azionario statunitense. |
| YoY | Year-over-Year | Variazione rispetto allo stesso periodo dell'anno precedente. |
| ZIRP | Zero Interest Rate Policy | Politica monetaria con tassi prossimi allo zero. |

---

## 22. Glossario dei concetti

### Adapter

Implementazione tecnica di una porta. Esempi: lettore JSON, archivio su file, client FRED o Yahoo. Può essere sostituito senza cambiare il significato del dominio.

### Allocation Proposal

Proposta di pesi o scostamenti compatibile con IPS e vincoli. Non è un ordine né una decisione automatica.

### Allocation Policy Engine

Componente logico che traduce il regime operativo in tilt consentiti, rispettando allocazione strategica, bande e limiti.

### Allocazione strategica

Composizione di lungo periodo del portafoglio. È l'ancora da cui parte ogni proposta tattica.

### API key

Segreto usato per autenticarsi presso un servizio. Non deve essere salvato in Git, log o ricevute.

### As-of Date

Data alla quale viene ricostruita la conoscenza disponibile. Coincide con il confine informativo dell'analisi.

### Atomicità

Proprietà per cui un'operazione appare completata interamente oppure non eseguita, evitando artefatti parziali.

### Audit trail

Traccia verificabile di dati, versioni, passaggi, review e decisioni.

### Availability Date

Data in cui un'informazione è realmente utilizzabile dal sistema, non soltanto il periodo a cui si riferisce.

### Backtest

Simulazione storica di un metodo. È utile soltanto se rispetta tempi dell'informazione, costi e separazione tra training e test.

### Baseline Model

Modello semplice e trasparente usato come benchmark permanente e fallback.

### Bande strategiche

Limiti minimi e massimi ammessi per ogni classe di attivo.

### Brier Score

Errore quadratico medio delle probabilità previste per eventi binari. Più è basso, migliore è la calibrazione complessiva.

### Calibration o calibrazione

Coerenza tra probabilità previste e frequenze osservate. Se eventi stimati al 70% accadono circa sette volte su dieci, la previsione è ben calibrata.

### Challenger Model

Modello sperimentale che deve essere valutato contro la baseline con un protocollo congelato.

### Checkpoint

Documento formale che chiude uno step e registra prove, esito, limiti e passo successivo autorizzato.

### Classification threshold

Soglia oltre la quale una probabilità viene trasformata in una decisione o etichetta operativa.

### Composite Score

Punteggio ottenuto combinando più indicatori secondo pesi e regole versionati.

### Composition Root

Punto in cui le implementazioni concrete vengono collegate alle interfacce. Nel progetto è principalmente la CLI.

### Confidence

Misura della solidità del risultato, distinta dalla probabilità del regime vincente. Può includere margine, completezza e coerenza dei segnali.

### Cooldown

Periodo minimo prima di consentire una nuova variazione, per evitare reazioni eccessive.

### Cutoff

Istante oltre il quale nessuna informazione può entrare in una previsione.

### Data Card

Scheda che descrive una fonte: proprietà, frequenza, unità, calendario, vintage, trasformazioni, qualità e limiti.

### Data Gate

Controllo formale che impedisce l'uso di dati senza provenienza, significato e temporalità adeguatamente documentati.

### Data Leakage

Passaggio indebito di informazioni dal test o dal futuro al processo di costruzione del modello.

### Data Snapshot

Fotografia versionata degli input usati per una determinata analisi.

### Decision Record

Registrazione della decisione umana, delle evidenze considerate e delle eventuali deroghe.

### DeflationBust

Regime associato a contrazione severa e pressione deflazionistica o recessiva.

### Derived View

Vista ricostruibile a partire da artefatti primari, per esempio un indice. Non prevale sulla fonte autorevole.

### Determinismo

Proprietà per cui stessi input e stessa versione producono lo stesso risultato.

### Dimensione economica

Concetto misurato da una feature, per esempio crescita, inflazione, liquidità, credito o stress.

### Directory durability

Garanzia che anche l'aggiornamento della directory che contiene un file sia persistito dopo crash. È un requisito del futuro protocollo robusto.

### Downstream

Processi che consumano un artefatto prodotto a monte. Restano chiusi se il gate non li autorizza esplicitamente.

### Driver

Segnale che contribuisce in modo rilevante alla probabilità di un regime.

### Dry-run

Esecuzione di prova che verifica preparazione e artefatti senza attivare l'effetto operativo finale.

### Economic Feature

Indicatore calcolato da uno o più dati grezzi, con formula e significato economico espliciti.

### Expected Return

Rendimento atteso usato in un'ottimizzazione. È molto incerto e nella fase F dovrà essere ridotto prudentemente tramite shrinkage.

### Fail-closed

Regola secondo cui, in presenza di dubbio o prova mancante, la capacità resta disabilitata.

### Feature Set Version

Identificatore immutabile dell'insieme di feature e delle rispettive trasformazioni.

### Fingerprint del codice

Impronta che identifica la versione effettiva del codice usata per produrre un artefatto.

### Fold

Singola suddivisione temporale di training e test in una validazione walk-forward.

### Forward Return

Rendimento realizzato dopo la data della previsione. È un outcome e non può entrare nel PredictionLedger iniziale.

### Freshness

Età massima tollerata per un dato rispetto al cutoff.

### fsync

Operazione del sistema operativo che richiede la persistenza effettiva dei dati su storage; importante per la durabilità dopo un crash.

### GateDecision

Artefatto che registra l'esito formale di un gate e le sole azioni che esso autorizza.

### Gaussian HMM

HMM con emissioni gaussiane. È stato testato come challenger causale e train-only e non promosso.

### Goldilocks

Regime con crescita sufficientemente positiva e inflazione contenuta: né troppo caldo né troppo freddo.

### Ground Truth

Riferimento usato per valutare una previsione. Può essere autorevole ma ex-post e incompleto rispetto al fenomeno che si vuole misurare.

### Hash

Impronta deterministica di un contenuto. Permette di rilevare modifiche, non di certificare da sola la verità del contenuto.

### Hysteresis o isteresi

Uso di soglie diverse per entrare e uscire da uno stato, così da evitare oscillazioni frequenti.

### Idempotency Key

Identificatore di una richiesta che consente di riconoscere un retry e impedire duplicazioni.

### Idempotenza

Proprietà per cui ripetere la stessa operazione con gli stessi input non produce effetti aggiuntivi o divergenti.

### Information Cutoff

Confine temporale della conoscenza ammessa; sinonimo operativo di as-of date nel protocollo di previsione.

### Information Set

Insieme completo delle informazioni disponibili al cutoff.

### LateCycleOverheating

Regime di ciclo maturo con domanda, inflazione o condizioni finanziarie surriscaldate.

### Ledger

Registro ordinato di eventi o artefatti. Nel progetto conserva previsioni congelate e riferimenti di integrità.

### Lock

Meccanismo che impedisce a più processi di modificare contemporaneamente la stessa risorsa.

### Log Loss

Metrica che penalizza fortemente le probabilità molto sicure ma sbagliate.

### Look-ahead Bias

Errore che nasce quando una simulazione storica usa informazioni disponibili soltanto in futuro.

### Lookback

Intervallo storico usato per calcolare una feature.

### Macro Regime

Stato probabilistico sintetico dell'economia, descritto da crescita, inflazione, liquidità, credito e stress.

### Manifest

Elenco strutturato di artefatti, metadati, percorsi e hash necessari a verificarli o ricostruirli.

### Market Regime

Stato dei mercati finanziari, distinto dal contesto macroeconomico.

### Model Card

Scheda del modello con scopo, dati, feature, parametri, metriche, limiti, rischi e stato di promozione.

### Model Gate

Controllo formale che stabilisce se un modello può essere valutato, promosso o deve restare sperimentale.

### Model Version

Identificatore immutabile della logica, dei parametri e delle soglie del modello.

### Monotonicità

Proprietà per cui una versione o un contatore può soltanto avanzare, mai tornare indietro.

### needs_changes

Esito di review che richiede una remediation versionata prima di una nuova valutazione.

### no-follow

Regola di accesso ai file che impedisce di seguire collegamenti simbolici non attesi, riducendo rischi di sostituzione del percorso.

### No-go

Esito con cui un esperimento non viene promosso. Non è un fallimento del processo, ma evidenza da conservare.

### Observation Date

Periodo economico a cui un valore si riferisce.

### Operational Regime

Regime autorizzato per l'uso successivo dopo soglie di confidenza e regole prudenziali.

### Out-of-Sample

Valutazione su dati non usati durante addestramento o calibrazione.

### Point-in-time

Ricostruzione che usa soltanto informazione e vintage disponibili nel momento simulato.

### Polarity o polarità

Direzione economica di un indicatore: stabilisce se un aumento segnala miglioramento, deterioramento o dipende dal contesto.

### Port

Interfaccia definita dal nucleo per richiedere un servizio esterno senza dipendere dalla sua implementazione.

### Portfolio Regime

Stato operativo del portafoglio determinato da policy, vincoli e rischio; non coincide automaticamente con il macro regime.

### Precision

Quota delle segnalazioni positive che risultano corrette.

### PredictionLedger

Artefatto write-once che congela una previsione prima che l'outcome sia conoscibile.

### PredictionScore

Artefatto successivo che confronta la previsione congelata con l'esito osservato.

### Preflight

Serie di controlli obbligatori prima di un'operazione irreversibile o write-once.

### Preregistration o preregistrazione

Congelamento anticipato di ipotesi, metodo, metriche e soglie per impedire modifiche opportunistiche dopo l'esito.

### Primary Regime

Regime con la probabilità numericamente più alta prima delle regole operative di prudenza.

### Provider-neutral

Protocollo definito senza dipendere da un prodotto o fornitore specifico.

### Publication Date

Data ufficiale di pubblicazione di un'informazione.

### Recall

Quota degli eventi positivi reali che il modello riesce a identificare.

### Recovery

Procedura deterministica per riprendere dopo crash o fallimento parziale senza duplicare o corrompere lo stato.

### Reflation

Regime di ripresa o accelerazione della crescita accompagnato da risalita dell'inflazione.

### Regime

Rappresentazione sintetica e probabilistica di una configurazione economica o finanziaria.

### Regime Confidence

Valutazione della robustezza dell'assegnazione, separata dalla probabilità massima.

### Regime Explanation

Spiegazione strutturata di driver, segnali contrari, dati mancanti e warning.

### Regime Probability

Probabilità assegnata a un regime; l'insieme forma una distribuzione coerente.

### Regime Run

Record completo e persistito di un'esecuzione con input, versioni, risultato, proposta e audit.

### Release Gate

Controllo finale su qualità tecnica, documentazione, limiti e deviazioni prima di dichiarare una release.

### Remediation

Correzione formalizzata dei finding di una review, prodotta come nuova versione senza cancellare l'esito precedente.

### Reverse Stress Test

Analisi che parte da un esito avverso e cerca gli shock necessari a produrlo.

### Rollback

Ritorno a uno stato precedente. Nei registri monotoni può costituire una violazione di integrità.

### Runtime

Parte stabile del sistema che esegue i casi d'uso ordinari; è distinta dal laboratorio di ricerca.

### safely blocked

Stato in cui un disegno o una fase è correttamente chiuso, mentre una capacità pericolosa resta intenzionalmente non autorizzata.

### Segnale contrario

Indicatore che contraddice il regime dominante e deve essere mostrato nella spiegazione.

### ShadowIndex

Indice derivato dei ledger shadow. È ricostruibile e non è la fonte autorevole.

### Shadow-live

Valutazione prospettica in tempo reale senza esecuzione automatica delle decisioni.

### ShadowPreflight

Artefatto immutabile che registra i controlli effettuati prima di congelare la previsione mensile.

### Shrinkage

Riduzione prudenziale delle stime estreme verso valori più stabili, particolarmente utile per expected return incerti.

### State Machine

Modello che definisce stati ammessi e transizioni valide di un processo.

### Stagflation

Regime con crescita debole e inflazione elevata.

### Strategic Allocation Policy

Regole di lungo periodo che definiscono obiettivi, pesi, bande e limiti del portafoglio.

### Stress fattoriale

Scenario costruito applicando shock a fattori come tassi, spread, valute, azioni o correlazioni.

### Stress test storico

Applicazione del portafoglio o della strategia a episodi storici avversi.

### Taxonomy o tassonomia

Elenco versionato dei regimi e delle loro definizioni.

### Tilt

Scostamento limitato e temporaneo rispetto all'allocazione strategica.

### Train Gate

Controllo eseguito usando soltanto il training prima di osservare i risultati OOS.

### Training Window

Periodo storico utilizzato per stimare un modello o le sue soglie.

### Turnover

Quantità complessiva di portafoglio da comprare e vendere per passare dai pesi correnti a quelli proposti.

### UncertainTransition

Stato obbligatorio quando segnali, qualità informativa o confidenza non consentono una classificazione operativa robusta.

### Value Object temporale

Oggetto di dominio che rappresenta una data o un intervallo con regole esplicite, evitando ambiguità temporali.

### Vintage

Versione di una serie storica disponibile in uno specifico momento.

### Walk-forward Validation

Procedura che addestra sul passato e verifica sul futuro, avanzando progressivamente nel tempo.

### Write-once

Regola per cui un artefatto autorevole, una volta creato, non viene sovrascritto; un cambiamento richiede un nuovo artefatto.

### ZirpQeFinancialRepression

Regime caratterizzato da tassi prossimi allo zero, acquisti quantitativi e compressione dei rendimenti, con possibili effetti distorsivi sull'allocazione del capitale.

---

## Conclusione

Il Macro-Regime Engine non viene costruito come una “scatola nera che indovina il mercato”, ma come un sistema di conoscenza controllato. La priorità è sapere **quali dati sono stati usati, quando erano disponibili, quale versione li ha elaborati, quali limiti erano noti e chi ha autorizzato il passaggio successivo**.

La scelta più importante emersa nello sviluppo è che fermarsi correttamente può essere un risultato migliore che avanzare con prove insufficienti. Baseline, preregistrazione, review indipendente, artefatti write-once, gate e decisione umana servono tutti allo stesso obiettivo: rendere il processo comprensibile, ripetibile e prudente anche quando il futuro resta, inevitabilmente, incerto.
