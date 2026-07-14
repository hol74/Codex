# Model card - e13-financial-8ec8415452

## Ruolo

Candidato finanziario E13 selezionato come profilo `coverage`. Usa aggregazione
`noisy-or`, due mesi per l'ingresso e due per il recupero. La soglia LOEO
osservata e' `0,35`.

## Evidenza disponibile

- episode hit rate: `1,0` (3/3 episodi inner);
- mean episode recall: `0,88888889`;
- worst episode recall: `0,66666667`;
- false-positive rate sui controlli curati: `0,7826087`;
- threshold range tra leaveout: `0,0`.

## Limiti

L'elevata copertura e' ottenuta con un tasso di falsi allarmi incompatibile con
un uso operativo non filtrato. La cronologia contiene soltanto tre episodi
osservabili e resta ex-post. Il candidato non e' stato valutato sull'outer OOS,
non e' stato promosso e non puo' essere fuso con il ramo recessivo.

## Lifecycle

`research-rejected`; gate E13.4 `REJECTED_FOR_SHADOW` per
`maximumMeanControlFalsePositiveRate`. Promozione non autorizzata.
