# Checkpoint 0056 - E13.1 generatore vincolato

Data: 2026-07-14

## Obiettivo

Aprire un percorso di ricerca diverso dalle formule singole E12: congelare
prima una grammatica finita e generare una popolazione deterministica di
candidati, senza usarne i risultati per cambiare lo spazio di ricerca.

## Realizzato

- congelato `e13-candidate-generation-protocol-v1` sul foundation lock E12;
- separati i task `financial-stress-signal` e `recession-signal`, senza fusione;
- dichiarate prima della valutazione le scelte di aggregazione, persistenza di
  ingresso/uscita e tre soglie selezionabili esclusivamente nell'inner fit;
- implementato `e13-generate-candidates`, con validazione stretta del protocollo
  e output write-once;
- generato `e13-generated-candidates-v1`: 16 candidati univoci, 8 per task,
  tutti allo stato `research-generated` e non valutati;
- preregistrato il metodo successivo: leave-one-episode-out entro la sola
  inner validation, Pareto su qualita', stabilita' e complessita', massimo due
  elementi in shortlist per task.

## Identita' degli artefatti

- protocol SHA-256:
  `81e39ad49d41c2f886cb4ee222c70ed4041f3fe2cea1b1961969dc3101356b70`;
- generation id: `04493308138d10060df9dd99`;
- manifest SHA-256:
  `85c8bf00ff5c9a3ade2ff8a08af5795357d1562f1b2c7d97ae8ccf4c401f7810`.

## Decisione

E13.1 termina dopo la generazione: nessun candidato e' stato ordinato o
promosso. E13.2 dovra' implementare il valutatore LOEO leggendo il manifest
immutabile; non potra' ampliare la grammatica, riusare gli ID E12 o aprire
l'outer OOS.

## Verifica

- 2/2 test dedicati superati;
- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 45/45 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- determinismo byte-per-byte e ID univoci verificati;
- rifiuto di outer selection e cross-task fusion verificato;
- semantica write-once verificata.
