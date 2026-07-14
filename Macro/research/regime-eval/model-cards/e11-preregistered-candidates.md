# E11 - Model card di preregistrazione dei candidate

Data di freeze: 2026-07-14.

## Stato

Tre modelli `research-challenger` preregistrati. Nessuno e' ancora eleggibile
per lo shadow e nessun risultato inner/outer e' stato aperto al momento del
freeze. Il target massimo di E11 prima di outcome prospettici e'
`shadow-candidate`, non `operational-approved`.

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

Non ancora disponibili. Verranno aggiunti solo dopo implementazione, test e
freeze degli hash delle sorgenti.
