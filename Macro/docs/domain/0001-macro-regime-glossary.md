# Glossario Macro-Regime

Data: 2026-07-02

## Scopo

Questo glossario stabilizza il linguaggio del nuovo Macro-Regime Engine prima di creare lo scheletro C#. I termini qui definiti devono guidare naming, tipi di dominio, test e reportistica.

## Regime

Stato probabilistico del contesto economico-finanziario. Non e' una diagnosi certa e non deve essere ridotto a una singola etichetta se non per comunicazione sintetica.

Esempio:

```text
Goldilocks 34%, Reflation 26%, UncertainTransition 22%, Stagflation 11%, DeflationBust 7%
```

## Macro Regime

Regime dedotto da variabili macroeconomiche lente:

- crescita;
- inflazione;
- lavoro;
- credito;
- politica monetaria;
- ciclo economico.

Il macro regime cambia piu' lentamente del market regime.

## Market Regime

Regime dedotto da dati di mercato:

- trend;
- volatilita';
- spread credito;
- curve dei tassi;
- correlazioni;
- liquidita';
- momentum cross-asset.

Il market regime puo' anticipare o contraddire il macro regime.

## Portfolio Regime

Stato effettivo del portafoglio rispetto a:

- drawdown;
- concentrazione;
- rischio;
- liquidita';
- tracking error;
- distanza dalla policy strategica.

Il portfolio regime non coincide necessariamente con macro o market regime.

## As-of Date

Data rispetto alla quale il sistema deve ricostruire cosa era conoscibile. Ogni calcolo operativo deve avere una as-of date.

Regola:

```text
Nessun dato con publication date o availability date successiva alla as-of date puo' entrare nel calcolo.
```

## Observation Date

Data a cui si riferisce il fenomeno osservato.

Esempio:

```text
Inflazione di maggio 2026 -> observation date nel periodo maggio 2026
```

## Publication Date

Data in cui il dato e' stato pubblicato dalla fonte.

Esempio:

```text
Dato CPI di maggio pubblicato il 12 giugno.
```

## Availability Date

Data in cui il dato e' disponibile al sistema. Puo' coincidere con publication date oppure essere successiva per ragioni operative, ritardi di import o conferme.

## Vintage

Versione storica di un dato macro come era disponibile in una certa data. Serve a gestire revisioni e look-ahead bias.

## Data Snapshot

Insieme dei dati disponibili a una specifica as-of date. E' l'input informativo del calcolo.

## Feature

Trasformazione interpretata di una o piu' osservazioni. Una feature deve avere:

- codice;
- nome;
- dimensione economica;
- formula;
- polarita';
- peso;
- lookback;
- versione.

## Feature Set Version

Versione di un insieme di feature. Serve a sapere quali feature e formule erano attive in un run.

## Economic Dimension

Dimensione economica a cui una feature contribuisce. Le dimensioni iniziali sono:

- Growth;
- Inflation;
- Risk;
- Monetary;
- Credit;
- Liquidity.

Liquidity puo' partire come opzionale ma deve essere prevista dal modello.

## Model Version

Versione del modello di regime. Include:

- nome modello;
- versione;
- parametri;
- soglie;
- stato: baseline, challenger, retired;
- data di efficacia;
- limiti noti.

## Baseline Model

Modello rule-based interpretabile usato come riferimento minimo. Deve essere implementato prima dei modelli avanzati e rimanere benchmark permanente.

## Challenger Model

Modello sperimentale, per esempio HMM, clustering o ML. Puo' proporre probabilita' alternative ma non guida decisioni operative senza validazione e approvazione.

## Regime Run

Esecuzione di un modello a una specifica as-of date. Deve registrare:

- as-of date;
- execution timestamp;
- data snapshot id;
- feature set version;
- model version;
- input;
- probabilita';
- regime candidato;
- regime operativo;
- confidence;
- driver;
- segnali contrari;
- warnings.

## Regime Probability

Probabilita' assegnata a uno specifico regime. Deve essere compresa fra 0 e 1. La distribuzione complessiva deve essere normalizzata o esplicitamente marcata come non normalizzata.

## Regime Confidence

Misura della forza del regime operativo. Nella baseline iniziale puo' coincidere con la probabilita' piu' alta, ma in futuro potra' includere consenso, persistenza e qualita' dati.

## Regime Explanation

Spiegazione leggibile del perche' un regime o una probabilita' sono emersi. Deve includere driver principali, segnali contrari e impatto.

## UncertainTransition

Stato operativo obbligatorio quando:

- la confidence e' sotto soglia;
- i segnali divergono;
- mancano dimensioni critiche;
- il cambio regime non e' confermato;
- e' attivo un cooldown.

Non e' un errore. E' un risultato legittimo del sistema.

## Allocation Proposal

Proposta allocativa generata a partire da regime, policy strategica e vincoli. Non e' una decisione automatica.

Deve includere:

- tilt proposto;
- vincoli applicati;
- turnover stimato;
- costo stimato;
- impatto fiscale stimato se disponibile;
- motivazione;
- decisione suggerita.

## Strategic Allocation Policy

Ancora di lungo periodo del portafoglio personale. Include asset class, pesi target, bande min/max, cash minimo, turnover massimo e vincoli personali.

## Decision Record

Registrazione della decisione umana presa dopo una proposta allocativa. Deve includere:

- proposta;
- decisione;
- motivazione;
- eventuale override;
- timestamp;
- note.

## Driver

Feature o dimensione che spinge in modo rilevante il risultato del regime.

## Segnale contrario

Feature o dimensione che contraddice il regime principale o riduce la confidence.

## Cooldown

Periodo minimo di attesa dopo un cambio regime per evitare oscillazioni operative.

## Isteresi

Meccanismo per cui la soglia di ingresso in un regime e la soglia di uscita sono diverse. Serve a ridurre falsi segnali.
