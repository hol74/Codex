# Macro Regime - Fase E - Slice 6: v1.4 gates passed

Data di chiusura: 2026-07-13.

## Esito

La Slice E6 e' completata sul piano tecnico. La baseline `1.4-candidate` supera
il train gate v2 e, dopo autorizzazione del protocollo, supera anche l'audit OOS
senza violazioni.

Non viene dichiarata promozione operativa: il benchmark e' development/
validation gia' osservato, la ground truth NBER ha solo due mesi positivi OOS e
manca ancora uno shadow-live fresco.

## Modello

- mapping VIX logistico della v1.3;
- archetipi risk riallineati preservando i livelli VIX semantici v1.2;
- cutoff divergente tradotto allo stesso VIX 28,8;
- probabilita' su fit quadratico;
- confidence geometrica su fit assoluto e separazione relativa;
- threshold e penalita' invariati.

## Train gate

- integrita': pass;
- copertura: pass, 4 regimi;
- robustezza: 6/6 fold;
- incertezza aggregata: 2,38%;
- esito: eleggibile per apertura OOS.

## OOS

- 84 date uniche;
- audit: pass, zero violazioni;
- confidence media: 0,7045;
- incertezza: 2,38%;
- primary: Goldilocks 40, Reflation 33, DeflationBust 10,
  LateCycleOverheating 1;
- NBER operational: recall 100%, precision 20%, F1 33,33%, 8 falsi positivi.

La metrica NBER regredisce rispetto alla v1.1 operational e resta un limite
esplicito. Non viene eseguito tuning dopo l'apertura OOS.

## Verifiche

- build: 0 warning, 0 errori;
- test C#: 237 superati (Domain 93, Application 30, Infrastructure 87,
  Reporting 2, CLI 19, Web 6);
- test Python: 13 superati; compileall superato;
- nessun client HTTP in Domain/Application/Web;
- evaluation e report legati agli hash di dataset, piano, configurazioni e
  ground truth.

## Passaggio successivo

La v1.4 diventa baseline di ricerca congelata. La Fase E puo' riprendere con un
challenger temporale, confrontato contro v1.4, senza modificare nuovamente la
baseline sullo stesso OOS. In parallelo va predisposto shadow-live 2026+.
