# E11 - Model card di preregistrazione dei candidate

Data di freeze: 2026-07-14.

## Stato

Tre modelli `research-challenger` preregistrati. Al momento del freeze nessun
risultato era stato aperto. E11.2 ha successivamente valutato la sola baseline
v1.5 inner-only e l'ha respinta. Il target massimo di E11 prima di outcome
prospettici resta `shadow-candidate`, non `operational-approved`.

## Candidate

### baseline-v1-5-dimensional

Conserva geometria, confidence e soglie della v1.4. Aggiunge solo impulsi
causali mensili di financial stress e growth deterioration, con pesi semantici
fissi. Verifica se il blind spot dipende dall'assenza di dinamica nelle feature.

### changepoint-duration-v1

Usa innovazioni robuste train-only per riconoscere ingressi improvvisi e una
policy di durata/uscita esplicita. Verifica onset e recovery senza imporre la
persistenza geometrica del Gaussian HMM.

### rare-event-logit-v1

Benchmark supervisionato L2, deterministico e pesato per classe rara. Il solo
micro-sweep ammesso riguarda tre soglie dichiarate e avviene esclusivamente
nell'inner validation.

## Regole comuni

- massimo tre famiglie;
- outer OOS vietato per selezione, ranking o cambio dei parametri;
- trasformazioni e fitting train-only;
- causalita', label independence e determinismo obbligatori;
- Brier, log loss, average precision, calibrazione e diagnostica temporale;
- passaggio a shadow solo tramite gate E11 e revisione umana;
- ogni modifica richiede nuovo model id e nuovo manifest.

## Risultati

### baseline-v1-5-dimensional - E11.2

- copertura: 6 fold, 84 date inner-validation uniche, zero righe outer-test;
- scenari archetipici: 5/5 superati;
- recall/F1: invariati rispetto alla v1.4 (`1,0` / `0,33333333`);
- average precision: `0,41666667`, delta `+0,125`;
- Brier: `0,0344838`, delta `+0,00081972` (peggioramento);
- repo-stress protetto: `0/2` osservazioni conformi;
- esito: `REJECTED_FOR_SHADOW`.

Il report SHA-256 e'
`02ac093bbad8159b9f90941bd1307877ecec7c0a788c34b6913bed39ca2961a1`.
Non sono stati modificati pesi, soglie o geometria dopo l'esito. I risultati
dei due challenger E11.3 sono riportati sotto.

### changepoint-duration-v1 - E11.3

- copertura: 6 fold eleggibili, 84 date inner uniche;
- recall `1,0`, F1 `0,09090909`, 40 falsi positivi;
- Brier `0,22500048`, delta `+0,1913364`;
- ECE `0,44711367`, false-positive-run delta `+11` mesi;
- stress protetto `0/2`;
- esito `REJECTED_FOR_SHADOW`.

Report SHA-256:
`961625c71a20f14f881d7504961f9953c3c45059f6d6cffa9f33289ba92c449b`.

### rare-event-logit-v1 - E11.3

- copertura: 4 fold eleggibili su 6, 72 date inner uniche;
- due fold ineligibili per assenza di positivi nell'inner-fit;
- recall `0`, F1 `0`, nessun falso positivo e un falso negativo;
- Brier `0,01564579`, delta `-0,0134208`;
- average precision `0,01886792`, delta `-0,23113208`;
- tutti i fit eleggibili raggiungono il limite di 2000 iterazioni senza la
  tolleranza di convergenza; soglia selezionata `0,50`;
- esito `REJECTED_FOR_SHADOW`.

Report SHA-256:
`4bcc9719d1ae3d62d094819554fa51b15a84f6903e607902cf93834c6972786a`.

### Decisione E11.4

Zero candidati su tre sono eleggibili allo shadow. Nessun outer OOS e' stato
aperto e nessun parametro e' stato modificato dopo i risultati inner.
