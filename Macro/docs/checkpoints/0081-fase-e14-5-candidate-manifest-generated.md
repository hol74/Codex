# Checkpoint 0081 - E14.5 candidate manifest generated

Data: 2026-07-15

## Obiettivo

Espandere deterministicamente la grammatica E14.4l in un unico manifest
write-once di 40 candidati research, mantenendo chiusi fitting, evaluation,
ranking, composizione cross-meccanismo, outer OOS e promozione.

## Checkpoint Git iniziale

Prima di E14.5 e' stato consolidato il lavoro E14.4g2-E14.4l nel commit
`437ad0e` (`Complete E14 four-detector research foundation`). E14.5 parte
quindi da un confine Git esplicito.

## Enumerazione

| Meccanismo | Profili | Persistenze per profilo | Candidati |
| --- | ---: | ---: | ---: |
| banking-credit | 4 | 4 | 16 |
| broad-market-repricing | 4 | 4 | 16 |
| cross-border-growth | 1 | 4 | 4 |
| funding-liquidity | 1 | 4 | 4 |
| totale | 10 |  | 40 |

Ogni identita' deriva in forma canonica da protocollo, meccanismo, detector,
profilo, binding delle feature e parametri. I quantili `[0.80, 0.90, 0.95]`
sono conservati come opzioni di selezione train-inner e non costituiscono un
moltiplicatore dell'identita' del candidato.

## Confini verificati

- manifest generation: autorizzata;
- applicazione dei transform: non autorizzata;
- fitting, evaluation e ranking: non autorizzati;
- composizione cross-meccanismo: non autorizzata;
- outer OOS, promozione e mutazione tassonomia: non autorizzati;
- rischio vintage: ancora presente e confinato alla ricerca.

Il generatore non riceve label o dataset. Risolve ogni serie del profilo contro
un binding `populated-manifested` con `fitScope=inner-only` e rifiuta input non
legati esattamente agli hash congelati dal readiness audit E14.4l.

## Artefatti

- schema: `models/e14-four-detector-candidate-manifest-schema-v1.json`;
- contratto: `models/e14-four-detector-candidate-manifest-contract-v1.json`;
- manifest: `models/e14-generated-four-detector-candidates-v1.json`;
- modulo: `regime_eval/e14_candidate_generator.py`;
- comando: `e14-generate-candidates`;
- test: `tests/test_e14_candidate_generator.py`.

## Esito reale

- stato: `GENERATED_NOT_FIT_NOT_EVALUATED_OUTER_OOS_CLOSED`;
- generation ID: `c46fabacd7dcef9c05e8ecae`;
- candidati: 40, tutti con ID univoco;
- manifest SHA-256:
  `fcc72b9159cabf508aa392297f4e944f509e88ee2564013bb5c6a483365776cf`.

## Verifiche

- test mirati E14.5: 3/3;
- suite Python completa: 111/111;
- compilazione bytecode: superata;
- test .NET: superati;
- `git diff --check`: superato, restano soltanto gli avvisi di conversione
  LF/CRLF gia' noti nel workspace Windows.

## Prossimo passo

E14.6 deve preregistrare fold leave-one-episode-out, metriche per meccanismo,
regole di selezione delle soglie e condizioni di fallimento prima di eseguire
fitting o evaluation inner. Composizione e outer OOS devono restare chiusi.
