# Checkpoint 0112 - E14.7u metadata execution gate v2

Data: 2026-07-16

## Esito

Il gate fail-closed lega per hash il manifest v2, il request catalog v2, il
preregistration audit, il piano e lo schema chiuso. Verifica una credenziale
FRED senza persisterla e svolge sette probe metadata HTTPS limitati a 65.536
byte, con content type, marker e intera catena redirect vincolati alla
allowlist Federal Reserve, FDIC e FRED.

La prima esecuzione ha prodotto l'audit immutabile v2, SHA-256
`5b73864485a52a37ed5cc5d9a4e94cdc604938911fd2f35fabd9ee3ff9aeb616`:
sei probe superati e G.5 bloccato per marker `releaseDate` assente, pur con
risposta `200 application/json`. Nessuna autorizzazione e' stata concessa.

La struttura provider-primary effettiva espone `yearValue`, `Months`,
`MonthValue` e `Dates`. Il piano v3, SHA-256
`b8de2b978c529380dc3e1807df32fa0cc5ce713da2157d2b7117f48eebdbd2c6`,
lega l'audit bloccato e cambia soltanto il marker G.5 in `MonthValue`, oltre
agli identificatori di versione e ai metadati di remediation. Il retry ha
prodotto l'audit v3 SHA-256
`54f444fea108c355763044fbe060a765dd6099bc66345c33748fa21332b5b2f2`:
sette probe su sette superati, zero template eseguiti, zero osservazioni, zero
raw artifact, zero trasformazioni e nessuna lettura outer OOS.

Il reviewer indipendente ha inizialmente bloccato schema, redirect e topologia.
Dopo schema nested chiuso e applicato, rifiuto preventivo dei redirect
off-allowlist, snapshot root canonico, contract hash-bound e test avversariali,
ha approvato sia la materializzazione sia la remediation v3. Sono verdi nove
test mirati e l'intera suite di 246 test.

## Decisione

E' autorizzata soltanto una successiva esecuzione separata e atomica
dell'acquisizione contro gli hash esatti di manifest e catalogo v2. Il gate
non scarica dati sorgente. Trasformazione feature, generazione candidati,
evaluation e outer OOS restano vietati.
