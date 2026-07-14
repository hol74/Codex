# Checkpoint 0065 - E14.4b2 hard negative e review queue

Data: 2026-07-14

## Obiettivo

Colmare l'assenza di hard negative con prova affermativa per ogni meccanismo e
predisporre un processo verificabile di seconda revisione, senza attribuire
falsamente indipendenza al reviewer che ha costruito i dossier.

## Piano eseguito

1. cercare eventi materiali per i quali fonti ufficiali descrivono
   funzionamento ordinato o trasmissione contenuta;
2. richiedere per ogni hard negative narrativa ufficiale, osservazione
   quantitativa, due provider indipendenti e controevidenza;
3. congelare uno schema di ricevuta che lega reviewer e decisione all'hash del
   dossier;
4. generare i dossier hard-negative e una coda unica con positivi e controlli;
5. rifiutare auto-review, output sovrascritti e ricevute non hash-bound;
6. mantenere chiusi ground truth, corpus, outer OOS e candidati.

## Realizzato

- hard negative broad-market: Brexit, giugno-luglio 2016;
- hard negative funding-liquidity: Brexit, giugno-luglio 2016;
- hard negative cross-border-growth: Brexit, giugno-luglio 2016;
- hard negative banking-credit: crisi messicana, dicembre 1994-marzo 1995;
- fonti indipendenti BIS/Federal Reserve per Brexit e FDIC/Federal Reserve per
  il contrasto banking-credit;
- quattro dossier `reviewed` con `affirmativeOrderlyEvidence=true`;
- coda immutabile di 12 dossier: 8 positivi e 4 hard negative;
- schema chiuso per decisioni `accept`, `reject` e `needs-revision`;
- validazione dell'identita' del reviewer e rifiuto dell'autore del dossier;
- comando CLI `e14-adjudication-queue` e test dedicati.

## Esito

Stato: `INDEPENDENT_REVIEW_REQUIRED`.

- meccanismi con hard negative affermativo: 4/4;
- dossier in coda: 12;
- ricevute indipendenti: 0;
- dossier accettati indipendentemente: 0;
- righe outer utilizzate: 0;
- label scritte: 0;
- candidati generati: 0.

La copertura informativa e' migliorata: non siamo piu' privi di controlli
affermativi. La foundation non e' tuttavia ancora eleggibile, perche' la stessa
persona o agente che ha curato il pack non puo' certificarne l'accettazione.

## Limite statistico esplicito

Brexit produce tre dossier mechanism-specific ma rimane un solo shock
storicamente indipendente. In valutazione non potra' essere contato come tre
episodi distinti per stimare numerosita' o incertezza.

## Identita' degli artefatti

- hard-negative pack SHA-256:
  `b5d9fdc586db6e7be6d9b3f6ed55459a948d811975e43e5a92a77e019835f4d0`;
- independent-review schema SHA-256:
  `40601d88b91c39115104b59fba8248ee5423661bb4cb38886ad29dc4c38f6fb9`;
- review queue SHA-256:
  `8c4b0dbc3f401d48a463ed64342b0820eba50fb5958bd5c19303fff3c3617316`;
- adjudication audit SHA-256:
  `159f703e5faa83f8417276a656f7e6cbce841ece264b892354edddbbad1f055a`.

Gli artefatti autorevoli usano il suffisso runtime `v2`. La prima run `v1` e'
stata mantenuta immutabile ma superseded dopo aver irrigidito la validazione:
proprieta' extra sono vietate e una decisione `accept` richiede conferma
esplicita sia del claim di meccanismo sia dei confini.

## Prossimo passo

E14.4b3: consegnare la coda e le fonti a un reviewer realmente indipendente,
acquisire le ricevute firmate e rieseguire il gate. Solo dopo potra' essere
eseguito un separato label-foundation gate E14.4c.

## Verifica

- test mirati E14.4b2: 2/2 superati;
- `python -m unittest discover -s tests -v`: 64/64 superati;
- `dotnet test MacroRegime.slnx --no-restore`: 240/240 superati;
- `python -m compileall -q regime_eval tests`: superato;
- doppia generazione temporanea byte-identica;
- riuso degli output rifiutato;
- ricevuta firmata dall'autore rifiutata prima di scrivere artefatti.
