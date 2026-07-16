# Checkpoint 0097 - E14.7f proposta taxonomy post-2005 pronta per review

Data: 2026-07-16

## Obiettivo

Materializzare una proposta taxonomy post-2005 separatamente versionata, due
dossier banking-credit hash-bound e una queue write-once, senza mutare taxonomy
v5, accettare label o aprire dati e valutazioni.

## Artefatti congelati

- proposta: `us-financial-stress-post2005-v1`;
- proposta SHA-256:
  `73bc241078d7fb32196bdff3adec45932a1cf1f1cf3846721909a27af4aa814f`;
- queue SHA-256:
  `c5839d76422e3dd22bcf478a46bb6ca73da9bda32aec2aa15614fa40d9fa27da`;
- audit SHA-256:
  `7b9cf376728820c794a9324447eae3e2675c5a3ccd8adb31b516faca6c0d381b`;
- dossier: London Whale 2012 e Archegos 2021;
- receipt presenti: 0.

## Identita' e copertura

La proposta usa identificatori nuovi e conserva gli ID v5 soltanto come
riferimenti. Include:

- 6 episodi positivi post-cutoff e 10 assegnazioni meccanismo-evento;
- 6 righe hard-negative legacy, equivalenti a 2 controlli indipendenti per
  broad, cross-border e funding;
- 2 nuovi controlli banking-credit ancora in attesa di review indipendente;
- conteggi potenziali per meccanismo: positivi 2/4/2/2 e hard negative 2/2/2/2.

## Governance

- `us-financial-stress-v5.json` resta byte-identico;
- proposta e scope sono inattivi;
- i dossier sono `reviewed`, non `accepted`;
- self-acceptance vietata e almeno un reviewer indipendente richiesto;
- proposal, dossier e queue sono hash-bound e write-once;
- osservazioni, dataset, LOEO e outer OOS non sono stati letti;
- acquisizione, foundation, candidati, fitting, evaluation e promozione restano
  chiusi.

## Decisione

E' autorizzato soltanto E14.7g: handoff byte-identico della queue a un reviewer
indipendente e ingestion fail-closed di receipt v2 che combaciano con entrambi
gli SHA-256 dossier. Reject, needs-revision, receipt mancante o hash mismatch
non attivano lo scope.

## Verifiche

- test mirati E14.7f: 4/4;
- determinismo e write-once: superati;
- hash binding di proposta, dossier e queue: superato;
- nuovi ID disgiunti dagli event ID v5: superato;
- taxonomy v5 immutata: superato;
- regressione Python: 166/166;
- `compileall`: superato;
- test .NET eseguiti sui sei assembly: 240/240.
