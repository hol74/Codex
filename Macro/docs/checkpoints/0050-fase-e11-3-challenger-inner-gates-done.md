# Checkpoint 0050 - E11.3 challenger e chiusura E11.4

Data: 2026-07-14

## Obiettivo

Implementare i due challenger preregistrati, eseguirli soltanto sulle finestre
inner e chiudere il gate E11 senza usare l'outer OOS.

## Realizzato

- aggiunto il runner condiviso `regime_eval.e11_challengers`;
- implementato changepoint-duration con median/MAD train-only, filtro causale,
  durata e uscita esplicite;
- resa eseguibile senza parametri aggiuntivi la probabilita' changepoint,
  normalizzando sui due threshold dichiarati e usando la logistica standard;
- implementato rare-event logit L2 con livelli, differenze causali,
  standardizzazione train-only, peso positivo limitato e gradient descent
  deterministico;
- limitato il threshold selector alle sole soglie `0,25`, `0,35`, `0,50`;
- resi ineligibili i fold logit privi di positivi nell'inner-fit;
- vincolati input, gate e configurazioni al manifest E11.1;
- aggiunti comando CLI e test di determinismo, causalita', probabilita' e
  chiusura outer-test.

## Esiti

### Changepoint-duration v1

Il modello intercetta i due mesi positivi ma produce 40 falsi positivi. F1
scende a `0,09090909`, Brier sale a `0,22500048`, ECE a `0,44711367` e la
sequenza massima di falsi positivi peggiora di 11 mesi. Esito:
`REJECTED_FOR_SHADOW`.

Report SHA-256:
`961625c71a20f14f881d7504961f9953c3c45059f6d6cffa9f33289ba92c449b`.

### Rare-event logit v1

Quattro fold su sei sono eleggibili. Il modello non genera falsi positivi e
migliora il Brier, ma perde il positivo inner disponibile: recall e F1 sono
zero, average precision `0,01886792`. I fit eleggibili raggiungono 2000
iterazioni senza soddisfare la tolleranza. Esito: `REJECTED_FOR_SHADOW`.

Report SHA-256:
`4bcc9719d1ae3d62d094819554fa51b15a84f6903e607902cf93834c6972786a`.

## Decisione E11.4

Nessuno dei tre candidati E11 supera tutti i requisiti congiuntivi. Non viene
creato alcuno `shadow-candidate`, non viene aperto l'outer OOS e non vengono
modificati parametri in risposta ai risultati.

## Verifica

- `python -m compileall -q regime_eval tests`: superato;
- `python -m unittest discover -s tests -v`: 35/35 test superati;
- `dotnet build MacroRegime.slnx --no-restore`: superata, 0 warning e 0 errori;
- `dotnet test MacroRegime.slnx --no-restore --no-build`: 240/240 test superati;
- `git diff --check`: superato.
