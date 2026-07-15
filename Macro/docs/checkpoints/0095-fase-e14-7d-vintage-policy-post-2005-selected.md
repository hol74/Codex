# Checkpoint 0095 - E14.7d vintage policy post-2005 selected

Data: 2026-07-15

## Obiettivo

Scegliere il ramo successivo dopo il blocco E14.7c senza rilassare la causalita',
leggere dati o score, riaprire il no-go E14 o mutare taxonomy v5.

## Alternative valutate

1. chiudere definitivamente il ramo E14;
2. finanziare una ricostruzione archivistica provider-primary;
3. progettare uno scope post-2005 separatamente versionato.

La ricostruzione archivistica preserva lo standard ma non e' completabile
entro il 31 luglio ed e' rinviata a backlog. La chiusura e' valida ma non
selezionata, perche' uno scope recente mantiene una base positiva minima senza
alterare i risultati legacy.

## Decisione

Selezionato condizionalmente
`separately-versioned-post-2005-research-scope`, con cutoff immutabile
`2006-01-01`, derivato dalla disponibilita' dei metadata vintage e non dagli
esiti modello.

## Identificabilita'

Positivi post-cutoff:

- banking-credit: 2;
- broad-market-repricing: 4;
- cross-border-growth: 2;
- funding-liquidity: 2.

Sono preservati 6 eventi positivi unici e 10 assegnazioni meccanismo-evento.

Hard negative post-cutoff:

- banking-credit: 0;
- broad-market-repricing: 2;
- cross-border-growth: 2;
- funding-liquidity: 2.

Lo scope resta bloccato: servono almeno 2 hard negative banking-credit
indipendenti prima di qualsiasi proposta di nuova taxonomy.

## Evidenza

- osservazioni scaricate: 0;
- dataset e score LOEO letti: no;
- righe outer usate: 0;
- audit reale SHA-256:
  `98af6a7b301240d2ff9ba763dc1f4e579676774361237dc1c61296e1c64eda69`.

## Autorizzazione

E' autorizzato soltanto E14.7e: preregistrare fattibilita' dello scope recente,
nuova mappa source/vintage e almeno due dossier hard-negative banking. Taxonomy,
acquisizione, foundation, candidati, evaluation e outer OOS restano chiusi.

## Verifiche

- test mirati E14.7d: 4/4;
- regressione Python: 158/158;
- `compileall`: superato;
- test .NET `--no-restore`: superati;
- audit deterministico e write-once: superati;
- source hash e input hash: superati.
