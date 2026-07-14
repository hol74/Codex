# Model card - dual-timescale-regime-v1

Data di preregistrazione: 2026-07-14.

## Stato iniziale

Challenger di ricerca preregistrato, non eseguito al momento del freeze della
configurazione. Non e' una variante di k-means v1 o Gaussian HMM v1.

## Ipotesi

Il ciclo macro lento e lo stress finanziario rapido non devono condividere la
stessa persistenza. Il modello calcola quattro dimensioni osservabili, filtra
lentamente deterioramento della crescita/condizioni monetarie e rapidamente
risk appetite/credito, quindi combina causalmente le due componenti.

## Configurazione congelata

- slow contraction: 75% growth deterioration, 25% monetary restriction;
- EWMA lenta: alpha 0,25;
- fast stress: `1 - sqrt(RISK_APPETITE * CREDIT_STRESS)`;
- EWMA rapida: alpha 0,65;
- score recessivo: media geometrica delle due componenti filtrate;
- ingresso 0,55, uscita 0,45 con isteresi;
- nessun fitting su NBER o sulle label stress;
- test filtrato solo in avanti, inizializzato dalla storia train;
- aggregazione OOS: prima predizione del primo fold eleggibile.

## Protocollo e limiti

Il benchmark 2008-2025 e' gia' osservato e puo' produrre soltanto diagnostica di
sviluppo. NBER e stress v2 vengono letti dopo il freeze delle predizioni. Ogni
modifica successiva richiede un nuovo model id e una nuova preregistrazione.

La promozione richiede dati shadow-live freschi, Evidence Contract v2, utilita'
allocativa e revisione umana. Convergenza o miglioramento storico non bastano.

## Risultati

Sulle 84 date OOS uniche:

- TP 0, FN 2, FP 13, TN 69;
- recall 0%, precision 0%, F1 0%, balanced accuracy 42,07%;
- Brier score 0,15131507 e log loss 0,48335593;
- entrambi i mesi recessivi di marzo-aprile 2020 sono persi;
- il falso segnale persiste da maggio 2020 a maggio 2021.

Rispetto alla baseline operational v1.4: recall -100 punti percentuali, F1
-33,33 punti, 5 falsi positivi e 2 falsi negativi in piu'. La partizione stress
protetta v2 non allinea la dimensione financial stress su taper shock 2013 o
repo stress 2019; monetary restriction allinea invece i due mesi del taper.

Report locale SHA-256:
`2aa18e680f134f2b1a9586ac20dea879bce8e11604b9dc2dd9f50dc66ceaa899`.

## Decisione

Il challenger v1 e' respinto e conservato come risultato negativo. La
separazione dimensionale resta utile per la diagnosi, ma combinazione geometrica
e isteresi reagiscono troppo tardi e persistono troppo a lungo. Non si
modificano alpha, pesi o soglie sul benchmark osservato. Una nuova ipotesi
richiede un nuovo model id e dati prospettici per la decisione finale.
