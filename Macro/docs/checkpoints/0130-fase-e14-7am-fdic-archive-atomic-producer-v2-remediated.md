# Checkpoint 0130 - E14.7am FDIC archive atomic producer v2 remediated

Data: 2026-07-17

## Esito

E14.7am implementa una versione separata del producer che corregge i finding
della review E14.7al senza modificare gli artefatti hash-bound E14.7ak/al.

Producer v2:

- deserializza e valida direttamente gli stessi bytes del source catalog che
  vengono autenticati nell'audit;
- impone file name, raw hash e archive record ID univoci, oltre al binding del
  contenuto al quarter;
- rifiuta evidence di assenza marker-only e richiede una prova negativa
  esplicita e quarter-bound;
- rifiuta redirect con hop intermedi privi di evidenza response-level;
- valida un execution gate obbligatorio e usa nell'audit i bytes esatti di
  gate e schemi, senza ri-serializzarli;
- copia tutti i 79 raw nello staging e pubblica raw, manifest, map e audit con
  un solo rename della directory, ricontrollando gli hash prima della copia.

I 6 test avversari del producer e i 3 test dell'audit sono verdi. L'audit
E14.7am ha SHA-256
`c63e5bec08b915e85b370c893331c2baf2d6efe35d049a9288062bffaab4b121`.

## Decisione

Lo step ha eseguito zero rete, raccolto zero evidenze reali e pubblicato zero
bundle reali. Discovery catalog, execution gate operativo e source acquisition
restano chiusi. Il solo passo autorizzato e' la review indipendente E14.7an del
producer v2 e delle probe hash-bound.
