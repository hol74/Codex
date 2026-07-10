# Governance del progetto Macro-Regime

## Scopo

Questo documento definisce come governare il progetto Macro-Regime prima e durante l'implementazione C#. Il sistema deve supportare decisioni di asset allocation personale in modo probabilistico, auditabile e prudente. Non deve trasformarsi in un modello opaco che decide automaticamente il portafoglio.

Codex e' l'esecutore operativo del piano: legge i documenti, propone modifiche, implementa il codice, esegue test, aggiorna la documentazione e segnala blocchi, rischi o deviazioni dal piano.

## Documenti di riferimento

- `macro_regime.md`: base accademica e principi di dominio.
- `macro_regime_github.md`: benchmark di progetti open-source e gap rilevanti.
- `macro_regime_plan.md`: primo piano tecnico, da usare come input ma non come sequenza definitiva.
- `chat1.md`: decisione di reimpostazione del lavoro.
- `macro_regime_delivery_plan.md`: piano esecutivo e milestone.

## Principi non negoziabili

1. Il regime e' probabilistico, non una singola etichetta deterministica.
2. Macro regime, market regime e portfolio regime restano separati.
3. Lo stato `UncertainTransition` e' obbligatorio quando i segnali divergono.
4. La baseline rule-based viene implementata prima dei modelli avanzati.
5. HMM, clustering, Markov switching e modelli ML entrano prima come challenger, non come motore primario.
6. Ogni calcolo deve essere ricostruibile as-of date.
7. Ogni decisione allocativa deve essere subordinata a IPS, bande strategiche, turnover, costi, fiscalita' e liquidita'.
8. Nessuna proposta allocativa deve essere all-in/all-out o generare allocazioni estreme salvo policy esplicita.
9. Il sistema deve registrare cosa sapeva alla data della decisione.
10. Il dominio C# deve restare testabile senza database, UI, API esterne o file system.

## Separazione delle responsabilita' logiche

### Macro Regime Information System

Responsabilita':

- calcolare feature macro e market;
- stimare probabilita' dei regimi;
- identificare driver e segnali contrari;
- gestire transizione, persistenza e incertezza;
- produrre snapshot riproducibili.

Non deve:

- decidere direttamente pesi di portafoglio;
- ottimizzare un portafoglio;
- sostituire il giudizio umano.

### Allocation Policy Engine

Responsabilita':

- ricevere probabilita' di regime e scenari;
- applicare policy strategica e bande;
- calcolare tilt ammissibili;
- controllare turnover, costi, fiscalita' e liquidita';
- produrre una proposta spiegabile.

Non deve:

- ignorare l'asset allocation strategica;
- superare le bande senza autorizzazione;
- usare rendimenti attesi aggressivi non shrinkati.

### Decision and Governance Layer

Responsabilita':

- registrare run, input, output e versioni;
- conservare decisioni umane e motivazioni;
- mantenere audit trail;
- evidenziare blocchi di rischio;
- supportare review periodiche.

## Ruoli

### Owner umano

Responsabilita':

- approvare principi, policy e vincoli personali;
- decidere se accettare proposte allocative;
- validare trade-off fra rischio, costo, fiscalita' e obiettivi;
- approvare promozione di modelli challenger.

### Codex esecutore

Responsabilita':

- leggere i documenti prima di modificare codice o piano;
- mantenere coerenza con governance e delivery plan;
- implementare in piccoli incrementi verificabili;
- eseguire test e riportare risultati;
- aggiornare documentazione quando cambia una decisione;
- non introdurre modelli avanzati prima dei gate richiesti;
- segnalare esplicitamente rischi, assunzioni e debito tecnico.

### Baseline model

Ruolo:

- riferimento interpretativo minimo;
- benchmark contro cui confrontare modelli challenger;
- fallback operativo quando modelli avanzati non sono validati.

### Challenger model

Ruolo:

- modulo sperimentale nel research lab;
- puo' proporre probabilita' alternative;
- non puo' guidare allocazioni operative senza validazione e approvazione.

## Gate di progetto

### 1. Design Gate

Richiesto prima di introdurre componenti architetturali rilevanti.

Checklist:

- il problema e' descritto;
- sono indicate alternative considerate;
- e' spiegata la scelta;
- sono documentati impatti su test, dati, dominio e UI;
- la scelta rispetta separazione Domain/Application/Infrastructure.

Output atteso:

- nota nel documento di delivery o ADR dedicato se la decisione e' importante.

### 2. Data Gate

Richiesto prima di usare una serie o una feature.

Checklist serie:

- fonte;
- frequenza;
- unita';
- categoria economica;
- polarita';
- data osservazione;
- data pubblicazione;
- data disponibilita' stimata o reale;
- gestione revisioni/vintage.

Checklist feature:

- formula;
- dimensione macro;
- lookback;
- trasformazione;
- normalizzazione;
- polarita';
- peso;
- versione.

### 3. Model Gate

Richiesto prima di considerare un modello affidabile.

Checklist:

- scopo del modello;
- dati usati;
- feature usate;
- frequenza;
- parametri;
- soglie;
- periodo di validazione;
- metriche;
- limiti noti;
- casi in cui deve restituire `UncertainTransition`;
- confronto contro baseline.

### 4. Allocation Gate

Richiesto prima di generare una proposta allocativa.

Checklist:

- asset allocation strategica disponibile;
- bande min/max disponibili;
- turnover massimo disponibile;
- costo stimato disponibile;
- vincoli fiscali almeno rappresentabili;
- liquidita' minima/cash policy disponibile;
- motivazione naturale generata;
- nessuna violazione di policy.

### 5. Release Gate

Richiesto prima di considerare completata una milestone applicativa.

Checklist:

- build verde;
- test automatici verdi;
- seed demo riproducibile;
- report generato;
- documentazione aggiornata;
- limiti noti indicati;
- nessuna deviazione non documentata dalla governance.

## Model card minima

Ogni modello deve avere una scheda con:

- nome;
- tipo: baseline, challenger, retired;
- scopo;
- input;
- output;
- dati usati;
- frequenza;
- parametri;
- soglie;
- periodo di training;
- periodo di test;
- metriche;
- limiti noti;
- fallimenti noti;
- data ultima revisione;
- versione implementativa;
- owner decisionale.

## Data card minima

Ogni fonte dati deve avere una scheda con:

- nome fonte;
- provider;
- licenza o vincoli d'uso;
- frequenza;
- ritardo di pubblicazione;
- copertura storica;
- revisioni/vintage;
- campi acquisiti;
- trasformazioni applicate;
- rischi di qualita';
- fallback in caso di dato mancante.

## Audit trail minimo

Ogni `RegimeRun` deve registrare:

- run id;
- as-of date;
- execution timestamp;
- data snapshot id;
- feature set version;
- model version;
- input features;
- probabilita' per regime;
- regime candidato;
- regime confermato;
- stato di transizione;
- confidence;
- driver principali;
- segnali contrari;
- differenza rispetto al run precedente.

Ogni `AllocationProposal` deve registrare:

- proposal id;
- regime run id;
- policy version;
- portafoglio corrente;
- portafoglio target strategico;
- tilt proposto;
- vincoli applicati;
- vincoli violati o bloccanti;
- turnover stimato;
- costo stimato;
- impatto fiscale stimato se disponibile;
- decisione suggerita;
- spiegazione.

Ogni `DecisionRecord` deve registrare:

- decision id;
- proposal id;
- decisione umana;
- motivazione;
- eventuale override;
- timestamp;
- note.

## Regole per modifiche future

### Cambiare feature

Una feature puo' essere aggiunta o modificata solo se:

- ha una definizione scritta;
- ha polarita' esplicita;
- ha effetto atteso documentato;
- ha test su almeno un caso demo;
- non rompe run precedenti senza migrazione documentata.

### Cambiare soglie del baseline model

Una soglia puo' cambiare solo se:

- la motivazione e' documentata;
- il comportamento prima/dopo e' confrontato;
- i casi `UncertainTransition` sono verificati;
- il cambiamento non aumenta oscillazioni senza controllo.

### Promuovere un challenger

Un challenger puo' essere promosso solo se:

- batte la baseline su metriche predefinite;
- e' stato validato out-of-sample;
- ha stress test sui regimi peggiori;
- ha model card completa;
- produce spiegazioni sufficienti;
- e' approvato dall'owner umano.

## Regole operative per Codex

Quando Codex lavora sul progetto deve:

1. Controllare lo stato dei file e non sovrascrivere modifiche non richieste.
2. Tenere i cambiamenti piccoli e verificabili.
3. Preferire dominio e test prima di infrastruttura e UI.
4. Aggiornare il delivery plan quando una milestone cambia.
5. Riportare sempre cosa e' stato fatto, cosa e' stato testato e cosa resta rischioso.
6. Evitare dipendenze esterne nella baseline iniziale.
7. Non introdurre network/API reali finche' il seed demo non e' stabile.
8. Non introdurre ottimizzazione avanzata finche' non esiste una policy a bande.
9. Non introdurre modelli avanzati nel runtime finche' il research lab non li ha validati.

## Ritmo di revisione

- Revisione leggera a ogni milestone.
- Revisione tecnica quando cambia architettura, modello dati o baseline.
- Revisione trimestrale dei modelli.
- Revisione annuale della policy.
- Revisione straordinaria dopo drawdown, crisi di liquidita', cambio fiscale rilevante o fallimento evidente del modello.

## Rischi principali

| Rischio | Mitigazione |
|---|---|
| Look-ahead bias | As-of date, publication date, vintage e snapshot |
| Overfitting | Baseline semplice, walk-forward e challenger isolati |
| Modello opaco | Spiegazioni, driver e segnali contrari obbligatori |
| Turnover eccessivo | Isteresi, cooldown e soglie di intervento |
| Allocazioni estreme | Bande IPS e shrinkage |
| Confusione macro/market/portfolio | Moduli e tipi separati |
| UI prematura | Domain core e report prima della dashboard |
| Ricerca infinita | Milestone con DoD e gate |

## Stato iniziale approvato

La direzione iniziale e':

- implementare prima un domain core C# testabile;
- costruire una baseline rule-based interpretabile;
- rendere ogni run auditabile;
- generare proposte allocative vincolate, non decisioni automatiche;
- confinare modelli avanzati nel research lab fino a validazione.
