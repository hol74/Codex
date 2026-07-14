# Checkpoint 0061 - E14.2 tassonomia tri-state e label audit

Data: 2026-07-14

## Obiettivo

Versionare una tassonomia che distingua positivi, hard negative confermati,
ambigui e non etichettati, quindi verificare se la copertura consente di
generare nuovi candidati senza introdurre negativi impliciti.

## Realizzato

- creata `us-financial-stress-v3` senza modificare le ground truth precedenti;
- riclassificata soltanto evidenza gia' documentata in 6 episodi positivi e 2
  ambigui;
- separati i meccanismi broad-market repricing, funding/liquidity,
  banking/credit e cross-border/growth;
- fissata la precedenza `positive > hard-negative > ambiguous > unlabeled`;
- congelato il contratto del gate con minimi per episodi full, inner e hard
  negative per meccanismo;
- implementato un audit deterministico e write-once che legge dal dataset
  soltanto `asOfDate` per ricostruire il calendario inner;
- vietati negativi impliciti, accesso alle feature outer, generazione,
  ranking e promozione.

## Esito

L'inventario contiene 6 episodi positivi, 2 ambigui e zero hard negative. Nel
periodo inner sono osservabili 3 episodi positivi; le 84 date si dividono in 7
mesi positivi, 23 ambigui e 54 unlabeled.

Falliscono i requisiti di positivi full per meccanismo, positivi inner per
meccanismo, hard negative totali e hard negative per meccanismo. Il deficit
piu' ampio e' cross-border/growth: servono ancora 1 positivo full, 3 positivi
inner e 2 hard negative. Tutti i meccanismi richiedono 2 hard negative.

## Identita' degli artefatti

- tassonomia v3 SHA-256:
  `5c74072b70f6bc5c840b49e3937ffc0506db3a808adfd29138804e840fbf68b9`;
- label-audit contract SHA-256:
  `edee49028b9d8601c9d22bf956e4e8c8a393897c8d388f94c9d21a1d79d0d570`;
- report SHA-256:
  `821a9b503d6161fa73270b48ec659de8ca2306a324f50841f6d62c3f8346fcff`.

## Decisione

`NOT_READY_FOR_CANDIDATE_GENERATION`. L'exit code non zero del comando e' il
risultato atteso del gate. Il prossimo incremento e' E14.3: uno studio di
fattibilita' delle fonti storiche point-in-time e dei proxy compatibili, con
decisione go/no-go prima di popolare un nuovo corpus.

## Verifica

- test mirati E14.2: 2/2 superati;
- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 56/56 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- report deterministico e write-once;
- zero negativi impliciti e zero righe feature outer utilizzate;
- zero candidati, ranking, shortlist o promozioni.
