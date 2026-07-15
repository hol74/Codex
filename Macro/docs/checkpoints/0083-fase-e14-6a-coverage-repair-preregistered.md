# Checkpoint 0083 - E14.6a coverage repair preregistered

Data: 2026-07-15

## Obiettivo

Scegliere un percorso informativo verificabile per i tre meccanismi bloccati
da E14.6, senza abbassare retrospettivamente la storia minima, riusare outer
OOS o costruire splice fra metodologie differenti.

## Decisione

Il requisito di 60 mesi e le soglie minime di tre positivi e due hard negative
restano invariati. Sono preregistrate tre serie standalone:

| Meccanismo | Serie proposta | Copertura dichiarata | Positivi/HN proiettati |
| --- | --- | --- | ---: |
| banking-credit | FDIC failed/assisted assets mensili | 1934-2025 | 3/2 |
| cross-border-growth | `TWEXBMTH` variazione assoluta | 1973-2019 | 5/2 |
| funding-liquidity | Fed funds meno T-bill (`-TB3SMFFM`) | 1954-2025 | 3/2 |

La proiezione conserva i 16 candidate ID broad-market e sostituisce i 24 ID
ineligibili con 12 nuovi ID dopo un futuro lock foundation v2. Il budget
proiettato scende quindi da 40 a 28 candidati.

## Motivazione delle fonti

- FDIC BankFind dichiara una vista completa di fallimenti e transazioni di
  assistenza di istituzioni assicurate dal 1934. La somma mensile degli asset
  e' specifica per il meccanismo banking, ma e' un indicatore ritardato e gli
  zeri richiedono la verifica di completezza del registro.
- `TWEXBMTH` e' un indice broad trade-weighted mensile ufficiale della Federal
  Reserve. La serie termina nel 2019 ma tutti gli episodi cross-border della
  tassonomia terminano entro il 2016, quindi non serve alcuno splice.
- `TB3SMFFM` e' pubblicato dalla St. Louis Fed dal 1954. Il segno viene
  invertito affinche' maggiore flight-to-safety/pressione relativa corrisponda
  a maggiore stress. Non sostituisce semanticamente il TED e richiede una
  sensitivity analysis sul cambio della fonte Treasury del 2019.

Fonti ufficiali consultate:

- `https://banks.data.fdic.gov/explore/failures`;
- `https://fred.stlouisfed.org/series/TWEXBMTH`;
- `https://fred.stlouisfed.org/series/TB3SMFFM`;
- `https://www.chicagofed.org/research/data/nfci/about`;
- `https://www.chicagofed.org/publications/blogs/chicago-fed-insights/2020/nfci-revisions`.

## Alternative respinte

- riduzione post-hoc dei 60 mesi;
- splice delle serie interrotte con successori;
- fitting del solo broad-market;
- NFCI risk/credit come detector primari. I subindex NFCI hanno lunga storia e
  buona semantica, ma sono fattori ristimati settimanalmente e revisionabili;
  restano diagnostici, non sostituti causali primari.

## Esito

Stato:
`STRUCTURAL_COVERAGE_REPAIR_PREREGISTERED_MATERIALIZATION_REQUIRED`.

- fonti sostitutive: 3;
- candidati potenzialmente eleggibili: 28;
- source materialization: autorizzata;
- mutazione foundation v1: vietata;
- generazione candidati, fitting, evaluation, outer OOS e promozione: vietati.

Audit SHA-256:
`8d8bdc501c9fea6fbae2aa5a2537cf538e057126ced4758d45b7b78cd9a113da`.

## Verifiche

- test mirati E14.6a: 3/3;
- suite Python completa: 117/117;
- compilazione bytecode: superata;
- test .NET: superati;
- `git diff --check`: superato, con soli avvisi LF/CRLF gia' noti.

## Artefatti

- schema: `models/e14-structural-coverage-repair-plan-schema-v1.json`;
- piano: `models/e14-structural-coverage-repair-plan-v1.json`;
- contratto: `models/e14-structural-coverage-repair-contract-v1.json`;
- modulo: `regime_eval/e14_coverage_repair.py`;
- comando: `e14-preregister-coverage-repair`;
- test: `tests/test_e14_coverage_repair.py`.

## Prossimo passo

E14.6b deve scaricare snapshot ufficiali, congelarne gli hash e materializzare
foundation v2 e lock v2. Le coperture proiettate devono essere ricalcolate sui
dati reali e devono superare diagnostiche di revisione e confine metodologico
prima di versionare protocollo o manifest candidati.
