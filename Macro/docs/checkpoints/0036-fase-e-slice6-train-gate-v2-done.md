# Macro Regime - Fase E - Slice 6: train gate v2

Data: 2026-07-13.

## Obiettivo

Correggere il difetto strutturale del train gate v1 senza cambiare soglie o
parametri della baseline. Il v1 richiedeva integrita', copertura multiregime e
robustezza operativa in ogni singolo biennio, confondendo persistenza naturale
dei regimi e degenerazione del modello.

## Implementazione

Il gate v2 separa tre decisioni:

1. integrita' feature sulle date inner-validation uniche aggregate;
2. copertura dei regimi sulle stesse date uniche aggregate;
3. quota `UncertainTransition` per fold, con almeno 4 fold validi su 6.

Le date sovrapposte fra validation vengono contate una sola volta. Ogni fold
esclude il proprio outer test; nel rolling 10/2/1 una data test di un fold puo'
entrare nel train di un fold successivo. Il benchmark resta quindi development/
validation e non sostituisce un holdout finale o lo shadow-live.

La configurazione
`research/regime-eval/models/baseline-v1-2-train-gate-v2-preregistered.json`
e' stata congelata prima dell'esecuzione, mantenendo i limiti v1 e legandosi agli
hash di dataset ed evaluation v1.2.

## Risultato reale

Validation uniche: 84 date dal 2016-05-31 al 2023-04-28.

- copertura: superata; 4 regimi primari, Goldilocks dominante al 57,14%;
- robustezza operativa: superata; 5 fold su 6 entro il 50% di incertezza;
- integrita' feature: fallita; `RISK_APPETITE` ha boundary rate 27,38%, oltre
  il limite invariato del 25%;
- esito complessivo: non eleggibile per apertura OOS.

Le altre boundary rate aggregate sono entro soglia: growth 16,67%, monetary
10,71%, inflation 7,14%, credit 1,19%. Non viene alzato il limite dopo il
risultato. Il prossimo incremento deve pubblicare una nuova feature/model version
che ridisegni la normalizzazione VIX, con nuova preregistrazione train-only.

## Verifiche specifiche

- compatibilita' gate v1 preservata;
- test v2 con meno di tre regimi in ciascun fold ma tre regimi aggregati;
- deduplicazione delle date validation sovrapposte verificata;
- hash evaluation verificato dalla configurazione v2;
- test date dell'ultimo fold esclusa dall'aggregato;
- report negativo sempre scritto; nessun report OOS o NBER v1.2 aperto.

Verifica completa: build 0 warning/0 errori; 232 test C# superati (Domain 90,
Application 30, Infrastructure 85, Reporting 2, CLI 19, Web 6); 13 test Python
e compileall superati; nessun client HTTP nei layer Domain/Application/Web.
