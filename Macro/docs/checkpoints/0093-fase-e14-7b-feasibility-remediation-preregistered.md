# Checkpoint 0093 - E14.7b feasibility remediation preregistered

Data: 2026-07-15

## Obiettivo

Rimediare al gate E14.7a fallito senza acquisire dati, riutilizzare fonti
bloccate, rilassare la storia minima o scegliere sostituzioni sulla base dei
risultati LOEO/outer.

## Realizzato

- congelati schema, piano e contratto hash-bound E14.7b;
- preservate le 3 famiglie condizionali con task documentali verificabili;
- ritirate senza fallback le 5 famiglie bloccate;
- preregistrate 5 sostituzioni indipendenti e 7 fonti ufficiali;
- aggiunto il comando `e14-preregister-feasibility-remediation`;
- verificati meccanismo, scope episodi, unicita' della sostituzione, mancato
  riuso delle fonti bloccate e storia causale minima;
- mantenute chiuse acquisizione, foundation, candidati, fitting, evaluation,
  ranking, composizione, outer OOS e promozione.

## Remediation congelata

- banking: `bank-preexisting-structural-fragility` su annual historical
  summaries FDIC;
- broad: `broad-public-equity-valuation-drawdown` su Z.1 Fed e
  `broad-treasury-rate-dislocation` su DGS2/DGS10;
- funding: `funding-cd-tbill-tiering` su DCD90/DTB3 e
  `funding-primary-dealer-repo-balance` sulle statistiche primary dealer della
  New York Fed;
- cross-border: nessuna sostituzione; restano le due famiglie BIS condizionali.

## Esito

Tutte le 5 sostituzioni rispettano nominalmente i minimi causali congelati per
gli episodi applicabili. Questo controllo di calendario non prova accesso,
licenza, completezza componente, vintage, release semantics o stabilita'
metodologica e quindi nessuna famiglia e' ancora dichiarata `ready`.

Audit reale SHA-256:
`275cd32b58d12829e46542930be44fe1589931814c95c39a1be138c93b6b47a3`.

## Decisione

E' autorizzato soltanto E14.7c: re-audit metadata-only delle 3 famiglie
condizionali e delle 5 sostituzioni. Nessuna osservazione puo' essere scaricata
prima di un successivo contratto di acquisizione separato.

## Verifiche

- test mirati E14.7b: 4/4;
- regressione Python: 150/150;
- `compileall`: superato;
- test .NET con asset gia' ripristinati (`--no-restore`): superati;
- audit deterministico e write-once: superati;
- source hash e input hash: superati.
