# Checkpoint 0055 - E12.5 decisione indipendente

Data: 2026-07-14

## Obiettivo

Chiudere E12 senza fondere componenti privi di evidenza autonoma, conservando
gli esiti negativi e il lock dei dati come risultati riproducibili.

## Realizzato

- congelata `e12-independent-decision-v1` legando il foundation lock e gli hash
  dei due report inner-only;
- confermato `REJECTED_FOR_SHADOW` sia per
  `event-aware-financial-stress-v1` sia per `sahm-yield-hazard-v1`;
- vietata esplicitamente la composizione dei due segnali;
- confermato che nessuna riga outer OOS e' stata aperta e che non e' avvenuto
  tuning post-hoc;
- preservata la data foundation E12 come infrastruttura riutilizzabile, ma non
  le formule respinte.

## Decisione

E12 termina con zero candidati shadow e nessuna promozione operativa. Un nuovo
tentativo deve usare una fase, identificativi e preregistrazione nuovi. Il
percorso successivo dovra' generare una famiglia finita di candidati prima di
valutarli e selezionarli esclusivamente con dati inner.

## Verifica

- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 43/43 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- `git diff --check`: superato.
