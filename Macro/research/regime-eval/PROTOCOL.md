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
- `SAHM`: ricostruito dalle prime pubblicazioni `UNRATE`;
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

## Challenger previsti

Ordine iniziale: HMM, clustering, Markov switching, jump model. Ogni challenger
deve avere configurazione versionata, risultati out-of-sample e model card. I
risultati negativi vengono conservati.

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
