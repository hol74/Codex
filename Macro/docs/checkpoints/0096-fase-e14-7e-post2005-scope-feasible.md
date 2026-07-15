# Checkpoint 0096 - E14.7e scope post-2005 fattibile

Data: 2026-07-15

## Obiettivo

Verificare, senza osservazioni o score, se lo scope separato dal 2006 dispone
di controlli banking-credit indipendenti e di almeno una famiglia source/vintage
fattibile per ciascun meccanismo.

## Controlli banking preregistrati

1. `london-whale-contained-2012`, finestra aprile-luglio 2012;
2. `archegos-contained-2021`, finestra marzo-maggio 2021.

Le finestre non si sovrappongono ai positivi post-cutoff. Il rapporto del
Senato documenta l'evento London Whale; gli archivi FDIC QBP e H.8 permettono
una verifica sistemica indipendente. Per Archegos, la Federal Reserve documenta
il default, perdite concentrate soprattutto fuori dagli Stati Uniti e, in
pubblicazioni distinte, la resilienza del sistema bancario statunitense.

I due elementi sono candidati documentali, non label accettate.

## Audit source/vintage

Sono `ready` quattro famiglie, una per meccanismo:

- banking: release H.8 e QBP contemporanee archiviate;
- broad: DGS2-DGS10 con real-time period ALFRED post-2005;
- cross-border: release H.10 storiche non revisionate e regime 2019 esplicito;
- funding: DCPF3M-DTB3, con oltre 60 mesi di storia e break CP manifestati.

Le famiglie bloccate E14.7c non sono state promosse implicitamente. Le nuove
famiglie valgono soltanto per lo scope separato e restano non acquisite.

## Gate

- positivi: 2/4/2/2;
- hard negative dopo i candidati: 2/2/2/2;
- famiglie `ready`: 1/1/1/1;
- osservazioni scaricate: 0;
- dataset, LOEO e outer OOS letti: no;
- audit SHA-256:
  `0b4869ed5a774248b7223b41ac7e49d1624587bb2536857536eeb8e1736b27bd`.

## Decisione

Il gate di fattibilita' e' superato. E' autorizzato soltanto E14.7f:
preregistrare una proposta taxonomy post-2005 separata, costruire dossier
hash-bound per i due controlli e una queue write-once per review indipendente.

Taxonomy v5, attivazione scope, acquisizione, foundation, candidati, fitting,
evaluation, outer OOS e promozione restano chiusi.

## Verifiche

- test mirati E14.7e: 4/4;
- regressione Python: 162/162;
- `compileall`: superato;
- test .NET `--no-restore`: superati;
- audit deterministico, hash-bound e write-once: superato.
