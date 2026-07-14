# Model card - Baseline v1.1 candidate

Data valutazione: 2026-07-13.

## Stato

Research candidate non promossa. Supera i gate di saturazione e diversita', ma
fallisce il gate di copertura operativa per eccesso di `UncertainTransition`.
La baseline runtime non cambia.

## Dati e versioni

- corpus separato: `data/historical-real-v11-2008-2025/`;
- 213 snapshot mensili, 2008-04-30 - 2025-12-31;
- dataset SHA-256: `1a2db1c7540a2419757b37d01717de258548f9bcf301994dfcd5c83f47f17649`;
- feature set e modello: `1.1-candidate`;
- confirmation threshold: 0,55, invariata;
- raw regime score: invariati.

Il corpus aggiunge:

- `CPI_YOY`, calcolato dai livelli CPIAUCSL di prima pubblicazione ALFRED;
- `CPI_YOY_3M_CHANGE`, derivato usando soltanto valori disponibili ai cutoff
  corrente e precedente di tre mesi;
- `YC_10Y2Y_3M_CHANGE`, con la stessa policy point-in-time sui cutoff.

La curva, come le altre serie finanziarie giornaliere, usa storia FRED corrente
e non vintage. Questo limite resta esplicito.

Per CPI e INDPRO il trasformatore conserva esplicitamente il primo vintage di
ogni observation date prima di calcolare il tasso YoY; revisioni successive non
entrano nel corpus.

## Feature modificate

- inflazione: 30% T10YIE, 50% CPI YoY realizzato, 20% variazione trimestrale
  del CPI YoY;
- curva: 70% livello non monotono, 30% stabilita' della variazione trimestrale;
- growth, VIX, credito e formule di regime restano invariati.

## Risultati OOS unici

Campione: 84 date, 2018-04-30 - 2025-03-31.

- tutte le feature rispettano il limite di saturazione del 25%;
- Goldilocks: 70,24%, sotto il limite dell'80%;
- DeflationBust: 15,48%;
- Reflation: 14,29%;
- regimi primari osservati: 3;
- `UncertainTransition`: 75%, oltre il limite del 50%;
- gate falliti: 1;
- confidenza media: 0,4835.

Segnale recessivo operational:

- recall 100%;
- precision 28,57%;
- F1 44,44%;
- 5 falsi positivi e nessun falso negativo.

La ground truth OOS contiene ancora un solo episodio recessivo. Sull'intero
storico compaiono 4 mesi primari `Stagflation`, ma nessuno nell'OOS unico: non e'
evidenza sufficiente di classificazione multiregime efficace.

## Decisione e prossimo gate

Non promuovere e non modificare la soglia sullo stesso OOS. Le feature hanno
raggiunto una distribuzione accettabile; il collo di bottiglia residuo e' la
superficie dei raw score/confidence. Il prossimo incremento deve preregistrare
una nuova configurazione e stimarla esclusivamente su train/nested validation,
lasciando invariati i mesi OOS gia' osservati e preparando uno shadow-live 2026+.
