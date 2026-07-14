# Checkpoint 0058 - E13.3 shortlist Pareto

Data: 2026-07-14

## Obiettivo

Ridurre la popolazione finanziaria E13 a non piu' di due candidati
complementari, senza trasformare una scelta relativa in un gate di promozione.

## Realizzato

- congelato `e13-shortlist-contract-v1`, legato al report LOEO, al contratto di
  valutazione e al manifest generato;
- richiesta una copertura minima di 2/3 episodi prima della frontiera Pareto;
- calcolata la frontiera massimizzando hit rate e recall e minimizzando falsi
  positivi, instabilita' della soglia e complessita';
- selezionati deterministicamente un campione `coverage` e uno `precision`;
- registrate le ragioni di esclusione per tutti gli altri candidati;
- congelata una shortlist recessiva vuota per `INSUFFICIENT_EPISODES`;
- create le model card dei due candidati selezionati.

## Shortlist

1. `e13-financial-8ec8415452`, profilo `coverage`:
   - `noisy-or`, ingresso 2, recupero 2, soglia LOEO `0,35`;
   - 3/3 episodi colpiti, worst recall `0,6667`;
   - false-positive rate sui controlli `0,7826`.
2. `e13-financial-7452a93533`, profilo `precision`:
   - `top-two-mean`, ingresso 1, recupero 1, soglia LOEO `0,5`;
   - 2/3 episodi colpiti, worst recall `0`;
   - false-positive rate sui controlli `0,0435`.

Sei candidati finanziari superano il requisito minimo e appartengono alla
frontiera multidimensionale; i due scelti sono gli estremi dichiarati, non una
classifica universale. Gli altri due candidati non raggiungono 2/3 episodi.

## Identita' degli artefatti

- shortlist contract SHA-256:
  `4865f8a419ee45550e11e10a0b6158314e252f57a26705785583059a45b95014`;
- shortlist SHA-256:
  `c72b84fde31c7332499dc8f7c3097d7eb6564c1e842aaa3706f50cbb36fb13d7`.

## Decisione

Entrambi avanzano soltanto a `research-shortlisted`. E13.4 deve applicare gate
assoluti task-specifici e puo' respingerli entrambi. Non sono autorizzati
fusione, outer OOS, shadow lifecycle o promozione operativa.

## Verifica

- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 50/50 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- selezione deterministica byte-per-byte e write-once;
- massimo due candidati e ruoli distinti verificati;
- ramo recessivo con zero selezionati;
- rifiuto di contratti che autorizzano promozione.
