# Checkpoint 0128 - E14.7ak FDIC archive atomic producer implemented

Data: 2026-07-17

## Esito

E14.7ak corregge i bypass bloccanti rilevati dalla review E14.7aj con un
producer integrato, offline e fail-closed. Il nuovo percorso:

- valida source catalog, evidence manifest, map e audit contro schemi chiusi;
- applica nello stesso flusso i vincoli semantici sul roster 79/79;
- apre i file raw e ne verifica esistenza, dimensione, SHA-256, marker e, per
  i record risolti, archive record ID;
- impone request ID univoci, continuita' dei redirect e corrispondenza tra URL
  trimestrali e source catalog hash-bound;
- pubblica manifest, map e audit come unica directory, tramite staging sibling
  e rename atomico, eliminando lo staging in caso di errore.

Il ramo `confirmed-absent-provider-primary` e' coperto esplicitamente. La
failure injection pre-pubblicazione dimostra che non rimangono ne' target
parziali ne' directory di staging.

L'audit risultante ha SHA-256
`b2372432d20ff1bd759c8e8f0e65819ca89934a773bdbd783ec1898621db590d`;
il modulo implementativo ha SHA-256
`34c226a2015692497d406242da9d004a49161854960b3663a64918917b6ce5cd`.
Gli 8 test mirati e l'intera suite di 321 test Python sono verdi.

## Decisione

Il producer atomico e' implementato, ma non ancora approvato per la raccolta
reale. Lo step ha eseguito zero richieste di rete, raccolto zero righe reali e
pubblicato zero bundle reali. Discovery catalog, execution gate, catalogo v3,
source acquisition e snapshot v2 restano chiusi.

Il solo passo autorizzato e' E14.7al: review indipendente hash-bound del
validator integrato, dei binding al source catalog, del producer atomico e
della matrice di test avversaria.
