# Checkpoint 0048 - E11.1 preregistrazione candidate

Data: 2026-07-14

## Obiettivo

Congelare il laboratorio E11 prima dell'implementazione e impedire che il
benchmark outer OOS gia' osservato venga riutilizzato per tuning, selezione o
promozione.

## Realizzato

- aggiunto `e11-shadow-candidate-gate-v1`, con massimo tre candidati e target
  massimo `shadow-candidate`;
- preregistrate `baseline-v1-5-dimensional`, `changepoint-duration-v1` e
  `rare-event-logit-v1` con policy causali e train-only;
- aggiunta model card comune senza risultati;
- implementato il comando `e11-preregister` e il validatore dei vincoli;
- generato `e11-preregistration-manifest.json` in modalita' write-once;
- aggiunti test di determinismo, ordine indipendente, immutabilita' e rifiuto
  della selezione outer OOS.

## Artefatto congelato

- registration id: `65d8d28f3d84e3e6cc995635`;
- SHA-256 manifest:
  `bc6b89eb6b38aa50118e79a77bca92aa21e9e8b7612ac920f25926054a6fcf8d`;
- SHA-256 gate:
  `60a801b2148ed67d57aa9b9cf537a6ab63726038636672d401d9ea875946eb4c`.

## Confine di lifecycle

Il superamento della futura validazione inner-only non costituisce promozione
operativa. Prima di nuovi outcome un modello puo' diventare soltanto
`shadow-candidate`. `operational-approved` richiede Evidence v2 prospettica e
decisione umana persistita.

## Verifica

- `python -m compileall -q regime_eval tests`: superato;
- `python -m unittest discover -s tests -v`: 30/30 test superati;
- `dotnet build MacroRegime.slnx --no-restore`: superata, 0 warning e 0 errori;
- `dotnet test MacroRegime.slnx --no-restore --no-build`: 240/240 test superati;
- `git diff --check`: superato.

Nessun modello E11 e' stato ancora implementato o valutato; il prossimo
incremento e' E11.2, baseline dimensionale v1.5.
