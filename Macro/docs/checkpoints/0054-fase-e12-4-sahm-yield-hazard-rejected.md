# Checkpoint 0054 - E12.4 SAHM yield hazard

Data: 2026-07-14

## Obiettivo

Preregistrare ed eseguire il candidato recessivo `sahm-yield-hazard-v1` con
ground truth NBER e gate separati dallo stress finanziario.

## Realizzato

- congelata una formula causale su SAHM, INDPRO YoY e transizione della curva;
- trailing window della curva limitata a osservazione corrente e 23 precedenti;
- nessun backward smoothing, fitting sulle label o durata post-hoc;
- creati gate e manifest write-once legati al foundation lock E12.2;
- generate probabilita' prima del collegamento delle label NBER;
- valutate 84 date inner uniche su 6 fold, con zero righe outer-test.

## Esito

Il candidato rileva aprile 2020, un mese dopo il primo campione recessivo, ma
perde marzo. Recall `0,5` e detection lag di un mese passano. La conferma
lagging di SAHM e INDPRO mantiene pero' il segnale elevato dopo il trough:

- F1 `0,13333333`, sotto `0,15`;
- average precision `0,0625`, sotto `0,10`;
- longest false-positive run 12 mesi, sopra il massimo 6;
- Brier `0,11911666` ed ECE `0,13514533` passano.

Esito finale: `REJECTED_FOR_SHADOW`.

## Artefatti

- config SHA-256:
  `b3b0c1b9c1e27baa2fd1e6ff1288af5cc1a0b07c83d58b5da402e1b2e8311052`;
- gate SHA-256:
  `3b95c4ef436f2d4fd7174bd650c2ed36d515e1ff7c69154a89e6223e108f36ce`;
- preregistration SHA-256:
  `f9f1dcffc2dd0e349ef13ab27f5bfc5fe5f73bbdd1b6a7ad134d5dc881008ac5`;
- report SHA-256:
  `15d935f8dbbcaccca6b23b37b172b6cdcbba19114b8c17375e90e9f1b294ab2a`.

## Decisione

Nessun tuning post-hoc e nessuna promozione. Il problema non e' la mancata
conferma della recessione, ma l'uscita tardiva dopo un episodio eccezionalmente
breve. E12.5 deve chiudere con una decisione indipendente sui due task; la
fusione resta vietata perché entrambi i componenti sono stati respinti.

## Verifica

- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 43/43 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- `git diff --check`: superato;
- test dedicati: causalita' rispetto ai dati futuri, transizione della curva,
  risposta SAHM/INDPRO e preregistrazione write-once.
